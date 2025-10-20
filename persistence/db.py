#!/usr/bin/env python3

from __future__ import annotations
import sqlite3
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from mailing.config import settings
from mailing.logging_config import logger


class DatabaseManager:
    """Менеджер базы данных SQLite."""
    
    def __init__(self, db_path: str = None):
        """Инициализирует менеджер базы данных."""
        self.db_path = db_path or settings.sqlite_db_path
        self._connection: Optional[sqlite3.Connection] = None
    
    def get_connection(self) -> sqlite3.Connection:
        """Получает подключение к базе данных."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self):
        """Закрывает подключение к базе данных."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Выполняет SQL запрос."""
        conn = self.get_connection()
        return conn.execute(query, params)
    
    def execute_many(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """Выполняет SQL запрос для нескольких наборов параметров."""
        conn = self.get_connection()
        return conn.executemany(query, params_list)
    
    def commit(self):
        """Сохраняет изменения."""
        if self._connection:
            self._connection.commit()
    
    def rollback(self):
        """Откатывает изменения."""
        if self._connection:
            self._connection.rollback()
    
    def __enter__(self):
        """Контекстный менеджер - вход."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход."""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


def init_database(db_path: str = None):
    """Инициализирует базу данных."""
    db_path = db_path or settings.sqlite_db_path
    
    # Создаем директорию если нужно
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    with DatabaseManager(db_path) as db:
        # Создаем таблицы
        create_tables(db)
        logger.info(f"Database initialized at {db_path}")


def create_tables(db: DatabaseManager):
    """Создает таблицы в базе данных."""
    
    # Таблица для отслеживания доставок
    db.execute("""
        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            template_name TEXT,
            subject TEXT,
            message_id TEXT,
            status TEXT NOT NULL,
            provider TEXT,
            error_message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delivered_at TIMESTAMP,
            opened_at TIMESTAMP,
            clicked_at TIMESTAMP
        )
    """)
    
    # Таблица для подавления email адресов
    db.execute("""
        CREATE TABLE IF NOT EXISTS suppressions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            reason TEXT,
            suppressed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица для отслеживания событий webhook'ов
    db.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            email TEXT,
            message_id TEXT,
            data TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица для дневных квот
    db.execute("""
        CREATE TABLE IF NOT EXISTS daily_quota (
            date TEXT PRIMARY KEY,
            sent_count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Индексы для производительности
    db.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_email ON deliveries(email)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_deliveries_sent_at ON deliveries(sent_at)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_events_email ON events(email)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_events_message_id ON events(message_id)")


# Глобальный экземпляр менеджера базы данных
_db_manager: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Получает глобальный экземпляр менеджера базы данных."""
    global _db_manager
    
    if _db_manager is None:
        db_path = settings.sqlite_db_path
        _db_manager = DatabaseManager(db_path)
        
        # Инициализируем базу если нужно
        init_database(db_path)
    
    return _db_manager


def close_db():
    """Закрывает глобальное подключение к базе данных."""
    global _db_manager
    
    if _db_manager:
        _db_manager.close()
        _db_manager = None


if __name__ == "__main__":
    # Инициализация базы данных
    init_database()
    print("✅ Database initialized successfully")
