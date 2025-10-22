#!/usr/bin/env python3

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path
import sqlite3
import logging

from src.mailing.config import settings

# Database schema constants - extracting magic strings
DELIVERIES_TABLE = "deliveries"
SUPPRESSIONS_TABLE = "suppressions"
EVENTS_TABLE = "events"

# SQL queries constants
CREATE_DELIVERIES_TABLE = """
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
"""

CREATE_SUPPRESSIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS suppressions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
"""

CREATE_EVENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        email TEXT NOT NULL,
        data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
"""

# Index creation for better performance
CREATE_INDEXES = [
    f"CREATE INDEX IF NOT EXISTS idx_{DELIVERIES_TABLE}_email ON {DELIVERIES_TABLE}(email)",
    f"CREATE INDEX IF NOT EXISTS idx_{DELIVERIES_TABLE}_created_at ON {DELIVERIES_TABLE}(created_at)",
    f"CREATE INDEX IF NOT EXISTS idx_{SUPPRESSIONS_TABLE}_email ON {SUPPRESSIONS_TABLE}(email)",
    f"CREATE INDEX IF NOT EXISTS idx_{EVENTS_TABLE}_email ON {EVENTS_TABLE}(email)",
    f"CREATE INDEX IF NOT EXISTS idx_{EVENTS_TABLE}_type ON {EVENTS_TABLE}(type)",
]

logger = logging.getLogger(__name__)


class DeliveryRepository:
    """Репозиторий для работы с результатами доставки."""
    
    # Schema version for migration strategy
    SCHEMA_VERSION = 1
    
    def __init__(self, db_path: str = None):
        """Инициализирует репозиторий."""
        self.db_path = db_path or settings.sqlite_db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализирует базу данных с миграциями и индексами."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create main table
                conn.execute(CREATE_DELIVERIES_TABLE)
                
                # Create indexes for better performance
                for index_sql in CREATE_INDEXES:
                    if DELIVERIES_TABLE in index_sql:
                        conn.execute(index_sql)
                
                # Check and handle schema migrations
                self._handle_schema_migrations(conn)
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def _handle_schema_migrations(self, conn: sqlite3.Connection):
        """Handle database schema migrations."""
        try:
            # Check current schema version
            cursor = conn.execute("PRAGMA user_version")
            current_version = cursor.fetchone()[0]
            
            if current_version < self.SCHEMA_VERSION:
                # Perform migrations
                cursor = conn.execute(f"PRAGMA table_info({DELIVERIES_TABLE})")
                columns = [row[1] for row in cursor.fetchall()]
                
                # Migration for missing columns
                if 'timestamp' not in columns:
                    conn.execute(f"ALTER TABLE {DELIVERIES_TABLE} ADD COLUMN timestamp TEXT")
                    logger.info("Added timestamp column to deliveries table")
                    
                if 'provider' not in columns:
                    conn.execute(f"ALTER TABLE {DELIVERIES_TABLE} ADD COLUMN provider TEXT")
                    logger.info("Added provider column to deliveries table")
                
                # Update schema version
                conn.execute(f"PRAGMA user_version = {self.SCHEMA_VERSION}")
                logger.info(f"Schema migrated to version {self.SCHEMA_VERSION}")
                
        except sqlite3.Error as e:
            logger.error(f"Schema migration error: {e}")
            raise
    
    def save_delivery(self, result) -> None:
        """Сохраняет результат доставки."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"""
                    INSERT INTO {DELIVERIES_TABLE} 
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
                logger.debug(f"Delivery result saved for {result.email}")
                
        except sqlite3.Error as e:
            logger.error(f"Error saving delivery result: {e}")
            raise
    
    def get_recent_deliveries(self, limit: int = 100) -> List[Dict]:
        """Получает недавние доставки."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(f"""
                    SELECT * FROM {DELIVERIES_TABLE} 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Error fetching recent deliveries: {e}")
            return []

    def get_delivery_stats(self) -> Dict[str, Any]:
        """Получает статистику доставок."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COALESCE(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END), 0) as successful,
                    COALESCE(SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END), 0) as failed
                FROM deliveries
            """)
            row = cursor.fetchone()
            
            total = row[0] if row else 0
            successful = row[1] if row else 0
            failed = row[2] if row else 0
            
            success_rate = (successful / total * 100) if total > 0 else 0.0
            
            return {
                'total': total,
                'successful': successful, 
                'failed': failed,
                'success_rate': success_rate
            }

    def get_deliveries_by_email(self, email: str) -> List[Dict]:
        """Получает доставки по email адресу."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM deliveries 
                WHERE email = ?
                ORDER BY created_at DESC
            """, (email,))
            return [dict(row) for row in cursor.fetchall()]

    def clear_old_deliveries(self, keep_recent: int = 1000):
        """Очищает старые доставки, оставляя только указанное количество."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM deliveries 
                WHERE id NOT IN (
                    SELECT id FROM deliveries 
                    ORDER BY created_at DESC 
                    LIMIT ?
                )
            """, (keep_recent,))
            conn.commit()


class SuppressionRepository:
    """Репозиторий для работы со списками подавления."""
    
    def __init__(self, db_path: str = None):
        """Инициализирует репозиторий."""
        self.db_path = db_path or settings.sqlite_db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализирует базу данных с индексами."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create suppressions table
                conn.execute(CREATE_SUPPRESSIONS_TABLE)
                
                # Create indexes for suppressions table
                for index_sql in CREATE_INDEXES:
                    if SUPPRESSIONS_TABLE in index_sql:
                        conn.execute(index_sql)
                
                conn.commit()
                logger.info(f"Suppressions table initialized at {self.db_path}")
                
        except sqlite3.Error as e:
            logger.error(f"Suppressions database initialization error: {e}")
            raise
    
    def is_suppressed(self, email: str) -> bool:
        """Проверяет, подавлен ли email (исключая отписки)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM suppressions WHERE email = ? AND reason != 'unsubscribe'",
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
    
    def add_suppression(self, email: str, reason: str = "manual", description: str = None) -> None:
        """Добавляет email в список подавления."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO suppressions (email, reason)
                VALUES (?, ?)
            """, (email, reason))
            conn.commit()

    def add_unsubscribe(self, email: str) -> None:
        """Добавляет email в список отписавшихся."""
        self.add_suppression(email, "unsubscribe")

    def remove_suppression(self, email: str) -> None:
        """Удаляет email из списка подавления."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM suppressions WHERE email = ?
            """, (email,))
            conn.commit()

    def get_all_suppressions(self) -> List[Dict]:
        """Получает все подавления."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT email, reason, created_at 
                FROM suppressions 
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]


class EventRepository:
    """Репозиторий для работы с событиями."""
    
    def __init__(self, db_path: str = None):
        """Инициализирует репозиторий."""
        self.db_path = db_path or settings.sqlite_db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализирует базу данных с индексами."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create events table
                conn.execute(CREATE_EVENTS_TABLE)
                
                # Create indexes for events table
                for index_sql in CREATE_INDEXES:
                    if EVENTS_TABLE in index_sql:
                        conn.execute(index_sql)
                
                conn.commit()
                logger.info(f"Events table initialized at {self.db_path}")
                
        except sqlite3.Error as e:
            logger.error(f"Events database initialization error: {e}")
            raise
    
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
