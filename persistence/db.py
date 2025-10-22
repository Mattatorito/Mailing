from __future__ import annotations
import sqlite3
from pathlib import Path
from mailing.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    success INTEGER NOT NULL,
    status_code INTEGER,
    message_id TEXT,
    error TEXT,
    provider TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    message_id TEXT,
    recipient TEXT,
    payload_json TEXT NOT NULL,
    signature_valid INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_events_message_id ON events(message_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
"""

_connection: sqlite3.Connection | None = None

def get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        db_path = settings.sqlite_db_path
        _connection = sqlite3.connect(db_path, check_same_thread=False)
        _connection.executescript(_SCHEMA)
        _connection.commit()
    return _connection
