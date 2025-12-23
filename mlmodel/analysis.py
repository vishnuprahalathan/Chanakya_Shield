from scapy.all import sniff, IP, TCP
import mysql.connector
import datetime
import joblib
import pandas as pd
import numpy as np
import requests
import warnings
import os

warnings.filterwarnings("ignore")

# Configuration
BOT_TOKEN = "8233619292:AAGDyAxVfDko_AEkNxMFaDWwhB4Wpx4sRIU"
CHAT_ID = "1115227029"
ALERT_ATTACKS = ["DoS Hulk", "PortScan", "DDoS", "Infiltration", "Bot", "Web Attack"] # Customize as needed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_models():
    try:
        iso_model = joblib.load(os.path.join(BASE_DIR, "anomaly_model.pkl"))
        rf_model = joblib.load(os.path.join(BASE_DIR, "attack_classifier.pkl"))
        scaler = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))
        selected_indices = joblib.load(os.path.join(BASE_DIR, "selected_features.pkl"))
        label_map = joblib.load(os.path.join(BASE_DIR, "attack_labels.pkl"))
        
        # Invert label map for decoding
        inv_label_map = {v: k for k, v in label_map.items()}
        
        return iso_model, rf_model, scaler, selected_indices, inv_label_map
    except FileNotFoundError as e:
        print(f"Error loading models: {e}")
        return None, None, None, None, None

iso_model, rf_model, scaler, selected_indices, inv_label_map = load_models()

def send_telegram_alert(src_ip, dest_ip, attack_type, reason):
    try:
        message = (
            f"PacketEyePro Alert\n"
            f"Time: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"Type: {attack_type}\n"
            f"Source: {src_ip}\n"
            f"Destination: {dest_ip}\n"
            f"Reason: {reason}"
        )
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=3)
    except Exception:
        pass

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="8883",
        database="packeteye"
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS packets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME,
        src_ip VARCHAR(45),
        dest_ip VARCHAR(45),
        protocol VARCHAR(10),
        length INT,
        flags INT,
        status VARCHAR(20),
        reason VARCHAR(255),
        attack_type VARCHAR(50)
    )
    """)
    conn.commit()
    conn.close()

init_db()

ALL_FEATURE_COLUMNS = [
    'Destination Port','Flow Duration','Total Fwd Packets','Total Backward Packets',
    'Total Length of Fwd Packets','Total Length of Bwd Packets',
    'Fwd Packet Length Mean','Bwd Packet Length Mean','Flow Packets/s',
    'FIN Flag Count','SYN Flag Count','RST Flag Count','PSH Flag Count',
    'ACK Flag Count','URG Flag Count','CWE Flag Count','ECE Flag Count'
]

def extract_features(packet):
    if not packet.haslayer(IP):
        return None

    length = len(packet)
    flags = int(packet[TCP].flags) if packet.haslayer(TCP) else 0

    # Note: Real-time flow feature extraction approx. 
    # For production, flow aggregation is needed.
    return {
        'Destination Port': packet[TCP].dport if packet.haslayer(TCP) else 0,
        'Flow Duration': np.random.randint(1000, 500000), 
        'Total Fwd Packets': np.random.randint(1, 50),
        'Total Backward Packets': np.random.randint(1, 50),
        'Total Length of Fwd Packets': length,
        'Total Length of Bwd Packets': length // 2,
        'Fwd Packet Length Mean': length,
        'Bwd Packet Length Mean': length / 2,
        'Flow Packets/s': np.random.uniform(0.1, 1000),
        'FIN Flag Count': flags & 0x01,
        'SYN Flag Count': (flags & 0x02) >> 1,
        'RST Flag Count': (flags & 0x04) >> 2,
        'PSH Flag Count': (flags & 0x08) >> 3,
        'ACK Flag Count': (flags & 0x10) >> 4,
        'URG Flag Count': (flags & 0x20) >> 5,
        'CWE Flag Count': 0,
        'ECE Flag Count': (flags & 0x40) >> 6,
    }

def process_packet(packet):
    if not iso_model:
        return

    try:
        if not packet.haslayer(IP):
            return

        src_ip = packet[IP].src
        dest_ip = packet[IP].dst
        proto = packet[IP].proto
        length = len(packet)
        flags = int(packet[TCP].flags) if packet.haslayer(TCP) else 0
        timestamp = datetime.datetime.now()

        features = extract_features(packet)
        if not features:
            return

        df = pd.DataFrame([features], columns=ALL_FEATURE_COLUMNS)
        
        # Preprocessing
        df_selected = df.iloc[:, selected_indices]
        X_scaled = scaler.transform(df_selected)

        # Hybrid Detection Logic
        # 1. Isolation Forest (Anomaly Detection)
        anomaly_score = iso_model.predict(X_scaled)[0] # -1 for anomaly, 1 for normal
        
        status = "Normal"
        reason = ""
        attack_type = "BENIGN"

        if anomaly_score == -1:
            status = "Anomaly"
            
            # 2. Random Forest (Classification)
            pred_idx = rf_model.predict(X_scaled)[0]
            attack_type = inv_label_map.get(pred_idx, "Unknown")
            
            if attack_type == "BENIGN": 
                # Conflict: IF says Anomaly, RF says Benign. 
                # Trust IF for zero-day potential or flag as Suspect.
                reason = "Statistical Anomaly (Unclassified)"
            else:
                reason = f"Classified as {attack_type}"

            if attack_type in ALERT_ATTACKS:
                send_telegram_alert(src_ip, dest_ip, attack_type, reason)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO packets
            (timestamp, src_ip, dest_ip, protocol, length, flags, status, reason, attack_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            timestamp, src_ip, dest_ip, str(proto),
            length, flags, status, reason, attack_type
        ))
        conn.commit()
        conn.close()

        print(f"{timestamp} | {src_ip} -> {dest_ip} | {status} | {attack_type}")

    except Exception:
        pass

if __name__ == "__main__":
    print("PacketEyePro Active. Press Ctrl+C to stop.")
    sniff(prn=process_packet, store=False)
