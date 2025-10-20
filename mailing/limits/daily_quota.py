#!/usr/bin/env python3

from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import sqlite3
from typing import Optional

from mailing.config import settings


@dataclass
class DailyQuota:
    """Класс для работы с дневными лимитами email отправки."""
    
    used_today: int = 0
    limit: int = 1000
    last_updated: Optional[str] = None
    
    def __init__(self, limit: int = 1000):
        """Инициализирует квоту."""
        self.limit = limit
        self.used_today = 0
        self.last_updated = None
        self._init_db()
    
    def _init_db(self):
        """Инициализирует базу данных для хранения квот."""
        db_path = Path(settings.sqlite_db_path)
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_quota (
                    date TEXT PRIMARY KEY,
                    used_count INTEGER DEFAULT 0,
                    limit_count INTEGER DEFAULT 1000
                )
            """)
            conn.commit()
    
    def load(self):
        """Загружает текущую квоту из базы данных."""
        today = date.today().isoformat()
        db_path = Path(settings.sqlite_db_path)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT used_count, limit_count FROM daily_quota WHERE date = ?",
                (today,)
            )
            row = cursor.fetchone()
            
            if row:
                self.used_today, self.limit = row
            else:
                # Создаем запись на сегодня
                conn.execute(
                    "INSERT INTO daily_quota (date, used_count, limit_count) VALUES (?, ?, ?)",
                    (today, 0, self.limit)
                )
                self.used_today = 0
            
            self.last_updated = today
    
    def register(self, count: int = 1):
        """Регистрирует отправку email."""
        today = date.today().isoformat()
        
        if self.last_updated != today:
            self.load()  # Перезагружаем квоту если день изменился
        
        self.used_today += count
        
        # Обновляем в базе данных
        db_path = Path(settings.sqlite_db_path)
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE daily_quota SET used_count = ? WHERE date = ?",
                (self.used_today, today)
            )
            conn.commit()
    
    def can_send(self, count: int = 1) -> bool:
        """Проверяет, можно ли отправить указанное количество email."""
        today = date.today().isoformat()
        
        if self.last_updated != today:
            self.load()  # Перезагружаем квоту если день изменился
        
        return (self.used_today + count) <= self.limit
    
    def remaining(self) -> int:
        """Возвращает количество оставшихся отправок на сегодня."""
        today = date.today().isoformat()
        
        if self.last_updated != today:
            self.load()
        
        return max(0, self.limit - self.used_today)
    
    def reset(self):
        """Сбрасывает использованную квоту на 0."""
        today = date.today().isoformat()
        self.used_today = 0
        
        db_path = Path(settings.sqlite_db_path)
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE daily_quota SET used_count = 0 WHERE date = ?",
                (today,)
            )
            conn.commit()
