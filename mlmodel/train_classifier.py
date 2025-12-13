import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib
import numpy as np

print("📥 Loading labeled dataset (CICIDS2017)...")
df = pd.read_csv(r"datasets/CICIDS2017_full.csv")


df.columns = df.columns.str.strip()


features = [
    'Destination Port','Flow Duration','Total Fwd Packets','Total Backward Packets',
    'Total Length of Fwd Packets','Total Length of Bwd Packets',
    'Fwd Packet Length Mean','Bwd Packet Length Mean','Flow Packets/s',
    'FIN Flag Count','SYN Flag Count','RST Flag Count','PSH Flag Count',
    'ACK Flag Count','URG Flag Count','CWE Flag Count','ECE Flag Count'
]


available = [col for col in features if col in df.columns]
missing = [col for col in features if col not in df.columns]

print(f"✅ Using {len(available)} available features.")
if missing:
    print(f"⚠️ Missing columns skipped: {missing}")


label_col = None
for c in df.columns:
    if c.lower() in ["label", "attack_cat", "attacktype", "class", "target"]:
        label_col = c
        break

if not label_col:
    raise ValueError("❌ Could not find any label column like 'Label' or 'Attack Category' in dataset!")

print(f"✅ Found label column: {label_col}")


df = df[available + [label_col]].copy()


print("🧹 Cleaning data (replacing inf, NaN, and large values)...")
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(inplace=True)

df[available] = df[available].clip(lower=-1e6, upper=1e6)

print(f"✅ Cleaned dataset shape: {df.shape}")


df[label_col] = df[label_col].astype('category')
df['Label_Code'] = df[label_col].cat.codes


X = df[available]
y = df['Label_Code']


scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)


X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

print("🚀 Training Random Forest classifier...")
clf = RandomForestClassifier(n_estimators=150, random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print("📊 Classification Report:\n", classification_report(y_test, y_pred))


joblib.dump(clf, "attack_classifier.pkl")
joblib.dump(scaler, "attack_scaler.pkl")
joblib.dump(df[label_col].cat.categories.tolist(), "attack_labels.pkl")

print("💾 attack_classifier.pkl, attack_scaler.pkl, attack_labels.pkl saved successfully.")
