import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import numpy as np

print("📥 Loading CICIDS2017 dataset...")
df = pd.read_csv(r"datasets/CICIDS2017_full.csv")
print(f"✅ Dataset loaded: {df.shape}")


df.columns = df.columns.str.strip()


selected_features = [
    'Destination Port',
    'Flow Duration',
    'Total Fwd Packets',
    'Total Backward Packets',
    'Total Length of Fwd Packets',
    'Total Length of Bwd Packets',
    'Fwd Packet Length Mean',
    'Bwd Packet Length Mean',
    'Flow Packets/s',
    'FIN Flag Count',
    'SYN Flag Count',
    'RST Flag Count',
    'PSH Flag Count',
    'ACK Flag Count',
    'URG Flag Count',
    'CWE Flag Count',
    'ECE Flag Count',
]


available = [col for col in selected_features if col in df.columns]
missing = [col for col in selected_features if col not in df.columns]

print(f"✅ Using {len(available)} available features.")
if missing:
    print(f"⚠️ Missing columns skipped: {missing}")

df = df[available].copy()

print("🧹 Cleaning data (handling inf / NaN / extreme values)...")
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(inplace=True)
df.reset_index(drop=True, inplace=True)


print(f"✅ Cleaned dataset shape: {df.shape}")
print(f"📊 Feature value ranges:\n{df.describe().T[['min', 'max']]}")


print("⚙️ Scaling feature values...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df)

print("🚀 Training Isolation Forest model (unsupervised anomaly detection)...")
model = IsolationForest(
    n_estimators=100,
    contamination=0.1,
    random_state=42
)
model.fit(X_scaled)
print("✅ Model training complete.")
print(f"🌲 Number of trees: {len(model.estimators_)}")


joblib.dump(model, "anomaly_model.pkl")
joblib.dump(scaler, "scaler.pkl")
print("💾 Model and scaler saved successfully at:")
print("   ➤ anomaly_model.pkl")
print("   ➤ scaler.pkl")
