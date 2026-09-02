import sqlite3
import datetime

DB_FILE = "recoverai_audit.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            channel TEXT,
            user_message TEXT,
            action_taken TEXT,
            original_amount REAL,
            payable_amount REAL,
            confidence_score REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_transaction(channel, user_message, action_taken, original_amount, payable_amount, confidence_score, status="RECOVERED"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (timestamp, channel, user_message, action_taken, original_amount, payable_amount, confidence_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        channel,
        user_message,
        action_taken,
        original_amount,
        payable_amount,
        confidence_score,
        status
    ))
    conn.commit()
    conn.close()

def fetch_latest_logs(limit=10):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, channel, user_message, action_taken, original_amount, payable_amount, confidence_score, status 
        FROM audit_logs ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

init_db()