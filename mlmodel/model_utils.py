import pandas as pd
import numpy as np

# Canonical 17-feature list for Chanakya Shield
ALL_FEATURE_COLUMNS = [
    'Destination Port', 'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
    'Total Length of Fwd Packets', 'Total Length of Bwd Packets',
    'Fwd Packet Length Mean', 'Bwd Packet Length Mean', 'Flow Packets/s',
    'FIN Flag Count', 'SYN Flag Count', 'RST Flag Count', 'PSH Flag Count',
    'ACK Flag Count', 'URG Flag Count', 'CWE Flag Count', 'ECE Flag Count'
]

def align_features(df, expected_columns, default_value=0.0):
    """
    Ensures the DataFrame matches the expected columns exactly.
    Handles missing, extra, and reordering.
    """
    # Force str type for all column names to prevent StandardScaler mismatches
    expected_columns = [str(c) for c in expected_columns]
    df.columns = [str(c) for c in df.columns]

    # 1. Add missing
    for col in expected_columns:
        if col not in df.columns:
            df[col] = default_value
            
    # 2. Select and reorder (drops extras)
    return df[expected_columns].copy()

def prepare_input_for_model(features, scaler_or_model, feature_names=None):
    """
    Universal adapter for model input.
    Returns a DataFrame perfectly aligned with the scaler/model's fitted names.
    """
    # 1. Get expected names
    expected_cols = getattr(scaler_or_model, "feature_names_in_", None)
    if expected_cols is not None:
        expected_cols = [str(c) for c in expected_cols]
    else:
        # Fallback to provided names
        if feature_names:
            expected_cols = [str(c) for c in feature_names]
        else:
            raise ValueError("No feature names found in model/scaler and no fallback provided.")

    # 2. Convert input features to DataFrame
    if isinstance(features, pd.DataFrame):
        df = features.copy()
    elif isinstance(features, (np.ndarray, list)):
        features_arr = np.array(features)
        if features_arr.ndim == 1:
            features_arr = features_arr.reshape(1, -1)
            
        # Case A: Input matches the fallback list (e.g. 17 features)
        if feature_names is not None and features_arr.shape[1] == len(feature_names):
             df = pd.DataFrame(features_arr, columns=[str(c) for c in feature_names])
        # Case B: Input matches the expected list (e.g. 15 features)
        elif features_arr.shape[1] == len(expected_cols):
             df = pd.DataFrame(features_arr, columns=expected_cols)
        else:
             raise ValueError(f"Feature shape {features_arr.shape[1]} doesn't match 17 or {len(expected_cols)}")
    else:
        raise TypeError(f"Unsupported features type: {type(features)}")
        
    # 3. Align and return
    return align_features(df, expected_cols)
