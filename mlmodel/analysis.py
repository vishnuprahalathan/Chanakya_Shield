from scapy.all import sniff, IP, TCP
import mysql.connector
import datetime
import joblib
import pandas as pd
import numpy as np
import requests
import warnings
import os

import os
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))

# Configuration
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
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "packeteye")
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

# Track flows for real feature extraction
flow_stats = {}

def extract_features(packet):
    if not packet.haslayer(IP):
        return None

    length = len(packet)
    flags = int(packet[TCP].flags) if packet.haslayer(TCP) else 0
    src_ip = packet[IP].src
    dest_ip = packet[IP].dst
    flow_key = tuple(sorted([src_ip, dest_ip]))

    now = datetime.datetime.now().timestamp()
    if flow_key not in flow_stats:
        flow_stats[flow_key] = {'start': now, 'fwd': 0, 'bwd': 0, 'len_fwd': 0, 'len_bwd': 0}
    
    stats = flow_stats[flow_key]
    duration = max(1, int((now - stats['start']) * 1000000)) # in microseconds
    
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
            # 2. Random Forest (Classification)
            pred_idx = rf_model.predict(X_scaled)[0]
            attack_type = inv_label_map.get(pred_idx, "Unknown")
            
            if attack_type == "BENIGN": 
                # High-sensitivity fix: If IF says Anomaly but RF is sure it's Benign,
                # mark as Normal to avoid scaring the user with home background traffic.
                status = "Normal"
                reason = "Background Noise (Filtered)"
            else:
                status = "Anomaly"
                reason = f"Classified as {attack_type}"

            if status == "Anomaly" and attack_type in ALERT_ATTACKS:
                send_telegram_alert(src_ip, dest_ip, attack_type, reason)

        # Balanced Logging: Log all for dashboard accuracy during dev/demo.
        # In high-traffic production, consider a separate stats table or sampling.
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
