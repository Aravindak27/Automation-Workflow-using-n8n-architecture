import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "stats.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at DATETIME,
            client_name TEXT,
            is_important BOOLEAN,
            email_subject TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_email(client_name, is_important, email_subject):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT INTO email_logs (received_at, client_name, is_important, email_subject)
        VALUES (?, ?, ?, ?)
    ''', (now_str, client_name, is_important, email_subject))
    conn.commit()
    conn.close()

def get_weekly_stats():
    now = datetime.utcnow()
    days_since_monday = now.weekday()
    last_monday = (now - timedelta(days=days_since_monday + 7)).replace(hour=0, minute=0, second=0, microsecond=0)
    last_sunday = last_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)

    last_monday_str = last_monday.isoformat()
    last_sunday_str = last_sunday.isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM email_logs 
        WHERE received_at >= ? AND received_at <= ?
    ''', (last_monday_str, last_sunday_str))
    total_emails = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COUNT(*) FROM email_logs 
        WHERE received_at >= ? AND received_at <= ? AND is_important = 1
    ''', (last_monday_str, last_sunday_str))
    important_emails = cursor.fetchone()[0]

    conn.close()

    return {
        "start_date": last_monday.strftime("%b %d, %Y"),
        "end_date": last_sunday.strftime("%b %d, %Y"),
        "total_emails": total_emails,
        "important_emails": important_emails
    }

# Initialize tables when imported
init_db()
