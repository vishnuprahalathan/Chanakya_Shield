from scapy.all import sniff, IP, TCP, conf
import mysql.connector
import datetime
import joblib
import pandas as pd
import numpy as np
import requests
import warnings
import os
import traceback
from dotenv import load_dotenv
from model_utils import prepare_input_for_model, ALL_FEATURE_COLUMNS

# 1. Setup
warnings.filterwarnings("ignore", category=UserWarning)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ALERT_ATTACKS = ["DoS Hulk", "PortScan", "DDoS", "Infiltration", "Bot", "Web Attack"]

def load_models():
    try:
        iso_model = joblib.load(os.path.join(BASE_DIR, "anomaly_model.pkl"))
        rf_model = joblib.load(os.path.join(BASE_DIR, "attack_classifier.pkl"))
        scaler = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))
        selected_indices = joblib.load(os.path.join(BASE_DIR, "selected_features.pkl"))
        label_map = joblib.load(os.path.join(BASE_DIR, "attack_labels.pkl"))
        inv_label_map = {v: k for k, v in label_map.items()}
        return iso_model, rf_model, scaler, selected_indices, inv_label_map
    except Exception as e:
        print(f"[!] Error loading models: {e}")
        return None, None, None, None, None

iso_model, rf_model, scaler, selected_indices, inv_label_map = load_models()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "packeteye")
    )

# Feature extraction logic
flow_stats = {}
def extract_features(packet):
    if not packet.haslayer(IP): return None
    length = len(packet)
    flags = int(packet[TCP].flags) if packet.haslayer(TCP) else 0
    src_ip, dest_ip = packet[IP].src, packet[IP].dst
    flow_key = tuple(sorted([src_ip, dest_ip]))
    now = datetime.datetime.now().timestamp()
    if flow_key not in flow_stats:
        flow_stats[flow_key] = {'start': now, 'fwd': 0, 'bwd': 0, 'len_fwd': 0, 'len_bwd': 0}
    stats = flow_stats[flow_key]
    duration = max(1, int((now - stats['start']) * 1000000))
    if src_ip == flow_key[0]:
        stats['fwd'] += 1
        stats['len_fwd'] += length
    else:
        stats['bwd'] += 1
        stats['len_bwd'] += length
    return {
        'Destination Port': packet[TCP].dport if packet.haslayer(TCP) else 0,
        'Flow Duration': duration, 
        'Total Fwd Packets': stats['fwd'],
        'Total Backward Packets': stats['bwd'],
        'Total Length of Fwd Packets': stats['len_fwd'],
        'Total Length of Bwd Packets': stats['len_bwd'],
        'Fwd Packet Length Mean': stats['len_fwd'] / max(1, stats['fwd']),
        'Bwd Packet Length Mean': stats['len_bwd'] / max(1, stats['bwd']),
        'Flow Packets/s': (stats['fwd'] + stats['bwd']) / max(0.001, (now - stats['start'])),
        'FIN Flag Count': flags & 0x01,
        'SYN Flag Count': (flags & 0x02) >> 1,
        'RST Flag Count': (flags & 0x04) >> 2,
        'PSH Flag Count': (flags & 0x08) >> 3,
        'ACK Flag Count': (flags & 0x10) >> 4,
        'URG Flag Count': (flags & 0x20) >> 5,
        'CWE Flag Count': 0,
        'ECE Flag Count': (flags & 0x40) >> 6,
    }

packet_count = 0
def process_packet(packet):
    global packet_count
    if not iso_model: return
    try:
        if not packet.haslayer(IP): return
        packet_count += 1
        if packet_count % 10 == 0: print(f"[*] Packets monitored: {packet_count}")
        
        src_ip, dest_ip = packet[IP].src, packet[IP].dst
        proto, length = packet[IP].proto, len(packet)
        flags = int(packet[TCP].flags) if packet.haslayer(TCP) else 0
        
        features = extract_features(packet)
        if not features: return
        features_list = [features[col] for col in ALL_FEATURE_COLUMNS]
        
        # Robust Preprocessing
        df_input = prepare_input_for_model(features_list, scaler, feature_names=ALL_FEATURE_COLUMNS)
        X_scaled = scaler.transform(df_input)
        df_scaled = pd.DataFrame(X_scaled, columns=[str(c) for c in scaler.feature_names_in_])

        # Detection
        anomaly_score = iso_model.predict(df_scaled)[0]
        status, attack_type, reason = "Normal", "BENIGN", ""
        
        if anomaly_score == -1:
            pred_idx = rf_model.predict(df_scaled)[0]
            attack_type = inv_label_map.get(pred_idx, "Unknown")
            if attack_type != "BENIGN":
                status, reason = "Anomaly", f"Classified as {attack_type}"
            else:
                reason = "Background Noise (Filtered)"

        # DB Logging
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO packets (timestamp, src_ip, dest_ip, protocol, length, flags, status, reason, attack_type)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (datetime.datetime.now(), src_ip, dest_ip, str(proto), length, flags, status, reason, attack_type))
            conn.commit()
            conn.close()
        except: pass

        # Dashboard Bridge
        try:
            eval_url = os.getenv("EVAL_SERVER_URL", "http://127.0.0.1:8001")
            requests.post(f"{eval_url}/api/inject-eval", json={
                "features": features_list,
                "true_label": 1 if status == "Anomaly" else 0,
                "attack_type": attack_type,
                "packet_id": packet_count
            }, timeout=0.1)
        except: pass

    except Exception as e:
        print(f"[-] Analysis Logic Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print(f"[*] Chanakya Shield Live Monitor Active on {conf.iface}")
    sniff(prn=process_packet, store=False)
