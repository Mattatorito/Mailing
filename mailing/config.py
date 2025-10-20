#!/usr/bin/env python3

from __future__ import annotations
from typing import Optional
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    """Класс настроек приложения с поддержкой переменных окружения."""

    # Resend API settings
    resend_api_key: str = ""
    resend_base_url: str = "https://api.resend.com"
    resend_from_email: str = "noreply@example.com"
    resend_from_name: str = "No Reply"

    # Application settings
    rate_limit_per_minute: int = 10
    max_retries: int = 3
    smtp_timeout: int = 30

    # Database settings
    sqlite_db_path: str = "mailing.sqlite3"

    @staticmethod
    def load() -> "Settings":
        """Загружает настройки из переменных окружения."""
        
        def _get(key: str, default=None, required=False):
            """Получает значение из переменных окружения."""
            val = os.getenv(key, default)
            if required and (val is None or val == ""):
                raise ValueError(f"Required environment variable {key} is not set")
            return val

        return Settings(
            resend_api_key=_get("RESEND_API_KEY", ""),
            resend_base_url=_get("RESEND_BASE_URL", "https://api.resend.com"),
            resend_from_email=_get("RESEND_FROM_EMAIL", "noreply@example.com"),
            resend_from_name=_get("RESEND_FROM_NAME", "No Reply"),
            rate_limit_per_minute=int(_get("RATE_LIMIT_PER_MINUTE", "10")),
            max_retries=int(_get("MAX_RETRIES", "3")),
            smtp_timeout=int(_get("SMTP_TIMEOUT", "30")),
            sqlite_db_path=_get("SQLITE_DB_PATH", "mailing.sqlite3")
        )

# Создаем глобальный экземпляр настроек
settings = Settings.load()

# Для обратной совместимости
Config = Settings
