from __future__ import annotations
from pathlib import Path
import sqlite3

from mailing.config import settings

"""
Database Connection and Schema Module

Этот модуль управляет подключением к SQLite базе данных и инициализацией схемы.
Предоставляет singleton connection для всего приложения."""


# SQL схема базы данных с полным описанием таблиц
_SCHEMA = """
-- Таблица результатов отправки email
CREATE TABLE IF NOT EXISTS deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,                    -- Email получателя
    success INTEGER NOT NULL,               -- 1 = успешно, 0 = ошибка
    status_code INTEGER,                    -- HTTP статус код от провайдера
    message_id TEXT,                        -- ID сообщения от провайдера
    error TEXT,                             -- Описание ошибки если есть
    provider TEXT,                          -- Имя провайдера (resend/dry-run)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица webhook событий от провайдеров
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,                 -- Провайдер отправивший webhook
    event_type TEXT NOT NULL,               -- Тип события (delivered/bounced/etc)
    message_id TEXT,                        -- ID сообщения
    recipient TEXT,                         -- Email получателя
    payload TEXT,                           -- Полный JSON payload
    signature_valid INTEGER DEFAULT 0,     -- Валидность подписи webhook
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_recipient ON events(recipient);

-- Таблица отписок от рассылок
CREATE TABLE IF NOT EXISTS unsubscribes (
    email TEXT PRIMARY KEY,
    reason TEXT,                            -- Причина отписки
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица подавления адресов (bounce, жалобы)
CREATE TABLE IF NOT EXISTS suppressions (
    email TEXT PRIMARY KEY,
    kind TEXT NOT NULL,                     -- bounce|complaint|manual
    detail TEXT,                            -- Детали подавления
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

# Глобальное подключение к БД (singleton pattern)
_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Возвращает singleton подключение к SQLite базе данных.

    При первом вызове создает подключение к БД, инициализирует схему
    и настраивает оптимизации. Последующие вызовы возвращают
    существующее подключение.

    Returns:
        sqlite3.Connection: Подключение к базе данных готовое к использованию
        
    Note:
        Использует check_same_thread = False для работы в многопоточном
        окружении, что безопасно при правильном использовании SQLite.

    Example:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deliveries")
        results = cursor.fetchall()
    """
    global _connection
    if _connection is None:
        db_path = settings.sqlite_db_path
        _connection = sqlite3.connect(db_path, check_same_thread = False)
        # Инициализируем схему БД
        _connection.executescript(_SCHEMA)
        _connection.commit()

        # Настройки оптимизации SQLite_connection.execute("PRAGMA journal_mode=WAL")  # Улучшенная конкурентность_connection.execute("PRAGMA synchronous=NORMAL")  # Баланс скорости/надежности_connection.execute("PRAGMA cache_size=10000")  # Увеличиваем кэш
        _connection.commit()

    return _connection
