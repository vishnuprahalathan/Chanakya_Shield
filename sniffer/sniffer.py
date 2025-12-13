from scapy.all import sniff, IP, TCP
import mysql.connector
import datetime

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
    status VARCHAR(10),   -- NULL until ML detects anomaly
    reason VARCHAR(255)   -- NULL until ML detects anomaly
)
""")
conn.commit()


def process_packet(packet):
    try:
        if packet.haslayer(IP):
            src_ip = packet[IP].src
            dest_ip = packet[IP].dst
            protocol = packet[IP].proto
            length = len(packet)
            flags = int(packet[TCP].flags) if packet.haslayer(TCP) else 0
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

           
            cursor.execute("""
                INSERT INTO packets (timestamp, src_ip, dest_ip, protocol, length, flags, status, reason)
                VALUES (%s, %s, %s, %s, %s, %s, NULL, NULL)
            """, (timestamp, src_ip, dest_ip, str(protocol), length, flags))
            conn.commit()

            print(f"{timestamp} | Proto:{protocol} | {src_ip} → {dest_ip} | Len:{length} | Flags:{flags}")

    except Exception as e:
        print("Error:", e)


print("Sniffing started... Packet capture in progress.")
sniff(prn=process_packet, store=False)
