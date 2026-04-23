import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "packeteye")
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM packets")
    count = cursor.fetchone()[0]
    print(f"Total packets in DB: {count}")
    
    cursor.execute("SELECT * FROM packets ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    print("Recent packets:")
    for row in rows:
        print(row)
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
