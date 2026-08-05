import sqlite3
import threading

from config import DATABASE_PATH

_lock = threading.Lock()


def _get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _lock:
        conn = _get_connection()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    snapshot_path TEXT NOT NULL,
                    lat REAL,
                    lon REAL,
                    session_duration REAL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()


def create_event(timestamp, confidence, snapshot_path, lat, lon):
    with _lock:
        conn = _get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO events (timestamp, confidence, snapshot_path, lat, lon)
                VALUES (?, ?, ?, ?, ?)
                """,
                (timestamp, confidence, snapshot_path, lat, lon),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()


def update_event_duration(event_id, duration):
    with _lock:
        conn = _get_connection()
        try:
            conn.execute(
                "UPDATE events SET session_duration = ? WHERE id = ?",
                (duration, event_id),
            )
            conn.commit()
        finally:
            conn.close()


def get_recent_events(limit=20):
    with _lock:
        conn = _get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()


def get_latest_event():
    events = get_recent_events(limit=1)
    return events[0] if events else None
