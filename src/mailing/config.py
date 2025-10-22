#!/usr/bin/env python3

from __future__ import annotations
from typing import Optional
import os
from dataclasses import dataclass
from dotenv import load_dotenv


def initialize_environment():
    """Explicit initialization point for loading environment variables."""
    load_dotenv()


@dataclass
class Settings:
    """Класс настроек приложения с поддержкой переменных окружения."""

    # Resend API settings  
    resend_api_key: str = "your_api_key"
    resend_base_url: str = "https://api.resend.com"
    resend_from_email: str = "noreply@example.com"
    resend_from_name: str = "No Reply"

    # Application settings
    rate_limit_per_minute: int = 10
    max_retries: int = 3
    smtp_timeout: int = 30
    concurrency: int = 5
    daily_limit: int = 100

    # Database settings
    sqlite_db_path: str = "test_mailing.sqlite3"
    templates_dir: str = "samples"
    
    def __post_init__(self):
        """Загружает и валидирует настройки из переменных окружения."""
        # Загружаем все настройки из переменных окружения
        self._load_from_environment()
        # Валидируем настройки
        self._validate_settings()
    
    def _load_from_environment(self):
        """Загружает все настройки из переменных окружения."""
        self.resend_api_key = os.getenv("RESEND_API_KEY", self.resend_api_key)
        self.resend_base_url = os.getenv("RESEND_BASE_URL", self.resend_base_url)
        self.resend_from_email = os.getenv("RESEND_FROM_EMAIL", self.resend_from_email)
        self.resend_from_name = os.getenv("RESEND_FROM_NAME", self.resend_from_name)
        
        # Преобразуем строковые значения в числовые
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", str(self.rate_limit_per_minute)))
        self.max_retries = int(os.getenv("MAX_RETRIES", str(self.max_retries)))
        self.smtp_timeout = int(os.getenv("SMTP_TIMEOUT", str(self.smtp_timeout)))
        self.concurrency = int(os.getenv("CONCURRENCY", str(self.concurrency)))
        self.daily_limit = int(os.getenv("DAILY_LIMIT", str(self.daily_limit)))
        
        self.sqlite_db_path = os.getenv("SQLITE_DB_PATH", self.sqlite_db_path)
        self.templates_dir = os.getenv("TEMPLATES_DIR", self.templates_dir)
    
    def _validate_settings(self):
        """Валидирует загруженные настройки."""
        if self.concurrency <= 0:
            raise ValueError("concurrency должно быть больше 0")
        if self.daily_limit <= 0:
            raise ValueError("daily_limit должно быть больше 0")
        if self.rate_limit_per_minute <= 0:
            raise ValueError("rate_limit_per_minute должно быть больше 0")
        if self.max_retries < 0:
            raise ValueError("max_retries не может быть отрицательным")
        if self.smtp_timeout <= 0:
            raise ValueError("smtp_timeout должно быть больше 0")
    
    def __repr__(self) -> str:
        """Безопасное представление настроек с маскировкой API ключа."""
        masked_key = "***" + self.resend_api_key[-4:] if len(self.resend_api_key) > 4 else "***"
        return (f"Settings("
                f"resend_api_key='{masked_key}', "
                f"resend_base_url='{self.resend_base_url}', "
                f"resend_from_email='{self.resend_from_email}', "
                f"resend_from_name='{self.resend_from_name}', "
                f"rate_limit_per_minute={self.rate_limit_per_minute}, "
                f"max_retries={self.max_retries}, "
                f"smtp_timeout={self.smtp_timeout}, "
                f"concurrency={self.concurrency}, "
                f"daily_limit={self.daily_limit}, "
                f"sqlite_db_path='{self.sqlite_db_path}', "
                f"templates_dir='{self.templates_dir}')")

    @staticmethod
    def load() -> "Settings":
        """Загружает настройки. Использует конструктор для избежания дублирования логики."""
        # Explicitly initialize environment before creating settings
        initialize_environment()
        # Создаем экземпляр с дефолтными значениями
        # __post_init__ автоматически загрузит все из переменных окружения
        return Settings()

# Создаем глобальный экземпляр настроек с explicit initialization
initialize_environment()
settings = Settings()

# Для обратной совместимости
Config = Settings
