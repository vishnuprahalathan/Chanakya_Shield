import os
import joblib
import pandas as pd
import numpy as np
import traceback

def run_diagnostic():
    print("=== Chanakya Shield ML Integrity Check ===")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    files_to_check = [
        "anomaly_model.pkl",
        "attack_classifier.pkl",
        "scaler.pkl",
        "selected_features.pkl",
        "attack_labels.pkl"
    ]
    
    loaded_objects = {}
    
    # 1. Check file existence and load
    for f in files_to_check:
        path = os.path.join(base_dir, f)
        if not os.path.exists(path):
            print(f"[FAIL] Missing file: {f}")
            continue
        try:
            obj = joblib.load(path)
            loaded_objects[f] = obj
            print(f"[OK] Loaded {f}")
        except Exception as e:
            print(f"[FAIL] Error loading {f}: {e}")

    if len(loaded_objects) < len(files_to_check):
        print("[!] Critical files missing. Cannot proceed with prediction test.")
        return

    # 2. Verify Feature Alignment
    scaler = loaded_objects["scaler.pkl"]
    rf_model = loaded_objects["attack_classifier.pkl"]
    
    try:
        scaler_features = scaler.feature_names_in_
        print(f"[INFO] Scaler expects {len(scaler_features)} features.")
        
        # Test a dummy prediction
        dummy_input = np.zeros((1, len(scaler_features)))
        df_dummy = pd.DataFrame(dummy_input, columns=scaler_features)
        
        X_scaled = scaler.transform(df_dummy)
        prob = rf_model.predict_proba(X_scaled)
        print(f"[OK] Dummy prediction successful. Output shape: {prob.shape}")
        
    except Exception as e:
        print(f"[FAIL] Feature alignment error: {e}")
        traceback.print_exc()

    # 3. Check Dataset for Evaluation Simulation
    dataset_path = os.path.join(base_dir, "..", "datasets", "payload_data_CICIDS2017_17features.csv")
    if os.path.exists(dataset_path):
        print(f"[OK] Simulation dataset found at {dataset_path}")
        try:
            df = pd.read_csv(dataset_path, nrows=5)
            print(f"[INFO] Dataset Columns: {list(df.columns)}")
        except Exception as e:
            print(f"[FAIL] Could not read dataset: {e}")
    else:
        print("[WARN] Simulation dataset NOT found. Background replay will fail.")

    print("=== Integrity Check Complete ===")

if __name__ == "__main__":
    run_diagnostic()
