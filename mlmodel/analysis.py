from scapy.all import sniff, IP, TCP
import mysql.connector, datetime, joblib, pandas as pd, numpy as np, requests


BOT_TOKEN = "8233619292:AAGDyAxVfDko_AEkNxMFaDWwhB4Wpx4sRIU"
CHAT_ID = "1115227029"
ALERT_ATTACKS = ["DoS Hulk", "PortScan", "DDoS", "Infiltration"]

def send_telegram_alert(src_ip, dest_ip, attack_type, reason):
    """Send alert to Telegram when a specific attack is detected."""
    try:
        message = (
            f"🚨 *PacketEyePro ALERT!*\n\n"
            f"🕒 *Time:* {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"💀 *Attack Type:* {attack_type}\n"
            f"📡 *Source IP:* {src_ip}\n"
            f"🎯 *Destination IP:* {dest_ip}\n"
            f"⚠️ *Reason:* {reason}"
        )
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except Exception as e:
        print("⚠️ Telegram alert error:", e)


conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="8883",
    database="packeteye"
)
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


print("📦 Loading models...")
iso_model = joblib.load("anomaly_model.pkl")
iso_scaler = joblib.load("scaler.pkl")
clf_model = joblib.load("attack_classifier.pkl")
clf_scaler = joblib.load("attack_scaler.pkl")
attack_labels = joblib.load("attack_labels.pkl")
print("✅ All models loaded successfully.")


selected_features = [
    'Destination Port','Flow Duration','Total Fwd Packets','Total Backward Packets',
    'Total Length of Fwd Packets','Total Length of Bwd Packets',
    'Fwd Packet Length Mean','Bwd Packet Length Mean','Flow Packets/s',
    'FIN Flag Count','SYN Flag Count','RST Flag Count','PSH Flag Count',
    'ACK Flag Count','URG Flag Count','CWE Flag Count','ECE Flag Count'
]


def extract_features(packet):
    if not packet.haslayer(IP):
        return None
    proto = packet[IP].proto
    length = len(packet)
    flags = int(packet[TCP].flags) if packet.haslayer(TCP) else 0
    dest_port = packet[TCP].dport if packet.haslayer(TCP) else 0

    return {
        'Destination Port': dest_port,
        'Flow Duration': np.random.randint(1000, 500000),
        'Total Fwd Packets': np.random.randint(1, 50),
        'Total Backward Packets': np.random.randint(1, 50),
        'Total Length of Fwd Packets': length,
        'Total Length of Bwd Packets': length // 2,
        'Fwd Packet Length Mean': length / np.random.randint(1, 10),
        'Bwd Packet Length Mean': (length / 2) / np.random.randint(1, 10),
        'Flow Packets/s': np.random.uniform(0.1, 1000),
        'FIN Flag Count': (flags & 0x01),
        'SYN Flag Count': (flags & 0x02) >> 1,
        'RST Flag Count': (flags & 0x04) >> 2,
        'PSH Flag Count': (flags & 0x08) >> 3,
        'ACK Flag Count': (flags & 0x10) >> 4,
        'URG Flag Count': (flags & 0x20) >> 5,
        'CWE Flag Count': 0,
        'ECE Flag Count': (flags & 0x40) >> 6,
    }


def process_packet(packet):
    try:
        if not packet.haslayer(IP):
            return

        src_ip, dest_ip = packet[IP].src, packet[IP].dst
        proto = packet[IP].proto
        length = len(packet)
        flags = int(packet[TCP].flags) if packet.haslayer(TCP) else 0
        
        timestamp = datetime.datetime.now().isoformat(timespec='seconds')

        features = extract_features(packet)
        if not features:
            return
        df = pd.DataFrame([features])

      
        X_iso = iso_scaler.transform(df)
        anomaly = iso_model.predict(X_iso)[0]
        status = "Anomaly" if anomaly == -1 else "Normal"

        reason = ""
        attack_type = None

        if status == "Anomaly":
            if length > 1500: reason = "Unusually large packet size"
            elif proto not in [6, 17, 1]: reason = f"Rare protocol {proto}"
            elif features['Flow Packets/s'] > 800: reason = "High packet rate"
            elif features['SYN Flag Count'] == 1 and features['ACK Flag Count'] == 0:
                reason = "Possible SYN flood"
            else:
                reason = "Statistical anomaly"

           
            X_clf = clf_scaler.transform(df)
            pred_code = clf_model.predict(X_clf)[0]
            attack_type = attack_labels[pred_code]

           
            if attack_type in ALERT_ATTACKS:
                send_telegram_alert(src_ip, dest_ip, attack_type, reason)

       
        cursor.execute("""
            INSERT INTO packets (timestamp, src_ip, dest_ip, protocol, length, flags, status, reason, attack_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (timestamp, src_ip, dest_ip, str(proto), length, flags, status, reason, attack_type))
        conn.commit()

     
        try:
            packet_data = {
                "timestamp": timestamp,
                "srcIp": src_ip,
                "destIp": dest_ip,
                "protocol": str(proto),
                "length": length,
                "flags": flags,
                "status": status,
                "reason": reason,
                "attackType": attack_type
            }
            
            requests.post("http://localhost:8080/api/packets", json=packet_data, timeout=2)
        except Exception as e:
            print("⚠️ Failed to send packet to backend:", e)

       
        if status == "Anomaly":
            print(f"🚨 {timestamp} | {src_ip}->{dest_ip} | Proto:{proto} | Len:{length} | {status} | {reason} | 🧠Attack:{attack_type}")
        else:
            print(f"✅ {timestamp} | {src_ip}->{dest_ip} | Proto:{proto} | Len:{length} | {status}")

    except Exception as e:
        print("⚠️ Error:", e)


print("🛰️ Hybrid Real-Time Packet Detection (Isolation Forest + Classifier + Telegram Alerts)...")
sniff(prn=process_packet, store=False)
