import sys
import os
import asyncio
import json
import random
import time
import pandas as pd
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import traceback
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)
loop = asyncio.get_event_loop()

# Setup Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis import load_models
from metric_engine import RealTimePacketMetricEngine
from quantum_pipeline import QuantumInspiredPipeline
from model_utils import prepare_input_for_model, ALL_FEATURE_COLUMNS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Metrics
classical_metrics = RealTimePacketMetricEngine("Classical Baseline")
quantum_metrics = RealTimePacketMetricEngine("Quantum-Inspired")
active_connections = set()

# Hardware/Model Init
iso_model, rf_model, scaler, selected_indices, inv_label_map = load_models()
quantum_pipeline = QuantumInspiredPipeline(rf_model, scaler, iso_model=iso_model)

async def process_and_broadcast(features, true_label, attack_type="Unknown", packet_id=0):
    """Bridge for both pipelines to dashboard."""
    t0 = time.time()
    
    try:
        # 1. Classical (RF Only) - Offload to thread pool
        def run_classical():
            df_input = prepare_input_for_model(features, scaler, feature_names=ALL_FEATURE_COLUMNS)
            X_scaled = scaler.transform(df_input)
            df_scaled = pd.DataFrame(X_scaled, columns=[str(c) for c in scaler.feature_names_in_])
            c_prob = rf_model.predict_proba(df_scaled)[0]
            return c_prob

        c_prob = await loop.run_in_executor(executor, run_classical)
        
        c_pred = 1 if (len(c_prob) > 1 and c_prob[1] > 0.5) else 0
        c_conf = c_prob[c_pred] if len(c_prob) > c_pred else 1.0
        c_latency = (time.time() - t0) * 1000
        classical_metrics.update(true_label, c_pred, c_latency, c_conf)

        # 2. Quantum (Iso + RF) - Offload to thread pool
        q_pred, q_conf, q_latency = await loop.run_in_executor(executor, lambda: quantum_pipeline.predict(features))
        quantum_metrics.update(true_label, q_pred, q_latency, q_conf)
        
        # 3. Payload Construction
        payload = {
            "packet_id": packet_id,
            "timestamp": str(time.time()),
            "classical": classical_metrics.get_metrics(),
            "quantum": quantum_metrics.get_metrics(),
            "explanation": quantum_pipeline.explain(q_pred, q_conf),
            "attack_type": attack_type
        }
        
        # 4. Broadcast
        if active_connections:
            # print(f"[*] Broadcasting to {len(active_connections)} clients...")
            disconnected = []
            for ws in active_connections:
                try:
                    await ws.send_json(payload)
                except:
                    disconnected.append(ws)
            for ws in disconnected: active_connections.remove(ws)

    except Exception as e:
        print(f"[-] Broadcast Error: {e}")
        traceback.print_exc()

@app.post("/api/inject-eval")
async def inject_eval(request: Request):
    data = await request.json()
    await process_and_broadcast(data.get("features"), data.get("true_label", 0), data.get("attack_type", "Live"), data.get("packet_id", 0))
    return {"status": "ok"}

@app.get("/api/reset-eval")
async def reset_eval():
    classical_metrics.reset()
    quantum_metrics.reset()
    print("[*] Metrics reset for fresh session.")
    return {"status": "reset"}

@app.websocket("/ws/evaluation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    print(f"[+] Client connected to Evaluation. Total: {len(active_connections)}")
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json({"heartbeat": True}) # Keep alive
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception:
        if websocket in active_connections: active_connections.remove(websocket)

# Demo Replay Loop
DATASET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datasets", "payload_data_CICIDS2017_17features.csv")

async def background_simulation():
    if not os.path.exists(DATASET_PATH): return
    
    print("[*] Starting Background Replay Loop...")
    df = pd.read_csv(DATASET_PATH, nrows=1000)
    df.columns = df.columns.str.strip()
    available_cols = [c for c in ALL_FEATURE_COLUMNS if c in df.columns]
    X = df[available_cols].values
    y = df['Label'].astype(str).apply(lambda x: 0 if x.upper() == "BENIGN" else 1).values
    
    idx = 0
    while True:
        if active_connections:
            feats = X[idx % len(X)]
            label = y[idx % len(y)]
            atype = df.iloc[idx % len(df)]['Label']
            await process_and_broadcast(feats, label, atype, idx)
            idx += 1
            await asyncio.sleep(0.5)
        else:
            await asyncio.sleep(2)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_simulation())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
