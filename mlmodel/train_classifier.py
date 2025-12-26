import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib

# =========================================================
# Load dataset (ROBUST PATH)
# =========================================================
print("📥 Loading labeled dataset (CICIDS2017)...")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "datasets", "CICIDS2017_full.csv")

df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip()

# =========================================================
# Feature list
# =========================================================
features = [
    'Destination Port','Flow Duration','Total Fwd Packets','Total Backward Packets',
    'Total Length of Fwd Packets','Total Length of Bwd Packets',
    'Fwd Packet Length Mean','Bwd Packet Length Mean','Flow Packets/s',
    'FIN Flag Count','SYN Flag Count','RST Flag Count','PSH Flag Count',
    'ACK Flag Count','URG Flag Count','CWE Flag Count','ECE Flag Count'
]

available = [c for c in features if c in df.columns]
print(f"✅ Using {len(available)} features.")

# =========================================================
# Detect label column
# =========================================================
label_col = None
for c in df.columns:
    if c.lower() in ["label", "attack_cat", "attacktype", "class", "target"]:
        label_col = c
        break

if not label_col:
    raise ValueError("❌ Label column not found!")

print(f"✅ Label column: {label_col}")

# =========================================================
# Cleaning
# =========================================================
df = df[available + [label_col]].copy()
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(inplace=True)
df[available] = df[available].clip(-1e6, 1e6)

print(f"✅ Cleaned dataset shape: {df.shape}")

# =========================================================
# Dataset sampling (memory safe)
# =========================================================
MAX_SAMPLES = 80000
if len(df) > MAX_SAMPLES:
    df = df.sample(n=MAX_SAMPLES, random_state=42)

print(f"📉 Training on dataset size: {df.shape}")

# =========================================================
# Encode labels
# =========================================================
df[label_col] = df[label_col].astype("category")
df["Label_Code"] = df[label_col].cat.codes

X = df[available].values
y = df["Label_Code"].astype(int).values

# =========================================================
# Scaling
# =========================================================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# =========================================================
# Train / test split
# =========================================================
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# =========================================================
# Train Random Forest
# =========================================================
print("🚀 Training Random Forest classifier...")
clf = RandomForestClassifier(
    n_estimators=80,
    max_depth=20,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=1
)

clf.fit(X_train, y_train)

# =========================================================
# Evaluation
# =========================================================
y_pred = clf.predict(X_test)
print("📊 Classification Report:\n")
print(classification_report(y_test, y_pred))

# =========================================================
# Save artifacts (Consistent with analysis.py)
# =========================================================
# Using dictionary for label_map to match train_model.py and analysis.py
categories = df[label_col].cat.categories.tolist()
label_map = {name: idx for idx, name in enumerate(categories)}

joblib.dump(clf, os.path.join(BASE_DIR, "attack_classifier.pkl"))
joblib.dump(scaler, os.path.join(BASE_DIR, "scaler.pkl"))
joblib.dump(label_map, os.path.join(BASE_DIR, "attack_labels.pkl"))

print("💾 Saved (Consistent with PacketEye system):")
print(f"   ➤ {os.path.join(BASE_DIR, 'attack_classifier.pkl')}")
print(f"   ➤ {os.path.join(BASE_DIR, 'scaler.pkl')}")
print(f"   ➤ {os.path.join(BASE_DIR, 'attack_labels.pkl')}")
