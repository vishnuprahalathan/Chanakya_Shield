import joblib
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def check_models():
    print("Checking models...")
    try:
        iso_model = joblib.load(os.path.join(BASE_DIR, "mlmodel", "anomaly_model.pkl"))
        rf_model = joblib.load(os.path.join(BASE_DIR, "mlmodel", "attack_classifier.pkl"))
        scaler = joblib.load(os.path.join(BASE_DIR, "mlmodel", "scaler.pkl"))
        
        print(f"Scaler features count: {len(scaler.feature_names_in_) if hasattr(scaler, 'feature_names_in_') else 'Unknown'}")
        if hasattr(scaler, 'feature_names_in_'):
            print(f"Scaler features: {list(scaler.feature_names_in_)}")
            
        print(f"RF model feature names count: {len(rf_model.feature_name()) if hasattr(rf_model, 'feature_name') else 'Unknown'}")
        if hasattr(rf_model, 'feature_name'):
            print(f"RF model feature names: {rf_model.feature_name()}")
            
        # Check Isolation Forest
        if hasattr(iso_model, 'feature_names_in_'):
             print(f"ISO model feature names: {list(iso_model.feature_names_in_)}")
        else:
             print("ISO model has no feature_names_in_")

    except Exception as e:
        print(f"Error checking models: {e}")

if __name__ == "__main__":
    check_models()
