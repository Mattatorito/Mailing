#!/usr/bin/env python3

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path
import sqlite3

from mailing.config import settings


class DeliveryRepository:
    """Репозиторий для работы с результатами доставки."""
    
    def __init__(self, db_path: str = None):
        """Инициализирует репозиторий."""
        self.db_path = db_path or settings.sqlite_db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализирует базу данных."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    status_code INTEGER,
                    message_id TEXT,
                    error TEXT,
                    provider TEXT,
                    timestamp TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def save_delivery(self, result) -> None:
        """Сохраняет результат доставки."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO deliveries 
                (email, success, status_code, message_id, error, provider, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result.email,
                result.success,
                result.status_code,
                getattr(result, 'message_id', ''),
                getattr(result, 'error', ''),
                getattr(result, 'provider', ''),
                getattr(result, 'timestamp', '')
            ))
            conn.commit()
    
    def get_recent_deliveries(self, limit: int = 100) -> List[Dict]:
        """Получает недавние доставки."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM deliveries 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]


class SuppressionRepository:
    """Репозиторий для работы со списками подавления."""
    
    def __init__(self, db_path: str = None):
        """Инициализирует репозиторий."""
        self.db_path = db_path or settings.sqlite_db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализирует базу данных."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS suppressions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def is_suppressed(self, email: str) -> bool:
        """Проверяет, подавлен ли email."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM suppressions WHERE email = ?",
                (email,)
            )
            return cursor.fetchone()[0] > 0
    
    def is_unsubscribed(self, email: str) -> bool:
        """Проверяет, отписан ли email."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM suppressions WHERE email = ? AND reason = 'unsubscribe'",
                (email,)
            )
            return cursor.fetchone()[0] > 0
    
    def add_suppression(self, email: str, reason: str = "manual") -> None:
        """Добавляет email в список подавления."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO suppressions (email, reason)
                VALUES (?, ?)
            """, (email, reason))
            conn.commit()


class EventRepository:
    """Репозиторий для работы с событиями."""
    
    def __init__(self, db_path: str = None):
        """Инициализирует репозиторий."""
        self.db_path = db_path or settings.sqlite_db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализирует базу данных."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    email TEXT,
                    data TEXT,
                    timestamp TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def save_event(self, event: Dict[str, Any]) -> None:
        """Сохраняет событие."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO events (type, email, data, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                event.get('type', ''),
                event.get('email', ''),
                str(event.get('data', '')),
                event.get('timestamp', '')
            ))
            conn.commit()
    
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Получает недавние события."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM events 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
