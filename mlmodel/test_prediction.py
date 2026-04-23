import os
import sys
import pandas as pd
import numpy as np
import joblib
import warnings

# Add current directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from analysis import load_models, ALL_FEATURE_COLUMNS
from quantum_pipeline import QuantumInspiredPipeline

def test_robust_prediction():
    print("--- Starting Robust Prediction Test ---")
    
    # 1. Load Models
    iso_model, rf_model, scaler, selected_indices, inv_label_map = load_models()
    if iso_model is None:
        print("Failed to load models. Ensure training is complete.")
        return

    # Initialize Quantum Pipeline
    qp = QuantumInspiredPipeline(rf_model, scaler, iso_model=iso_model)
    
    print(f"Expected features: {qp.expected_features}")
    
    # 4. Test Case 3: Full 17 Features (NumPy array)
    print("\nTest Case 3: Full 17 Features (NumPy array)")
    mock_full_features = np.random.rand(len(ALL_FEATURE_COLUMNS))
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            pred, conf, lat = qp.predict(mock_full_features)
            print(f"Prediction: {pred}, Confidence: {conf:.4f}")
            
            # Check for ANY sklearn warnings
            scikit_warns = [str(warn.message) for warn in w if "sklearn" in str(warn.filename).lower() or "UserWarning" in str(warn.category)]
            if scikit_warns:
                print(f"FAILURE: Warnings detected: {scikit_warns}")
            else:
                print("SUCCESS: Full 17-feature vector handled without warnings.")
    except Exception as e:
        print(f"Error in Test Case 3: {e}")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    test_robust_prediction()
