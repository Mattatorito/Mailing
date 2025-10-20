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
    sender_email: str = ""
    rate_limit_per_minute: int = 10
    max_retries: int = 3
    concurrency: int = 5
    sqlite_db_path: str = "mailing.sqlite3"
    log_level: str = "INFO"
    daily_email_limit: int = 1000
    list_unsubscribe: str | None = None
    resend_webhook_secret: str | None = None

    @staticmethod
    def load() -> "Settings":
        """Выполняет загрузку настроек.

        Returns:
            Settings: Результат выполнения операции
        """
        def _get(key: str, default=None, required=False):
            """Получает значение из переменных окружения.
            
            Args:
                key: Ключ переменной окружения
                default: Значение по умолчанию
                required: Обязательная ли переменная
                
            Returns:
                str: Значение переменной
            """
            val = os.getenv(key, default)
            if required and (val is None or val == ""):
                raise RuntimeError(f"Missing required environment variable: {key}")
            return val  # type: ignore

        resend_api_key = _get("RESEND_API_KEY", required=True)
        resend_base_url = _get("RESEND_BASE_URL", "https://api.resend.com")
        resend_from_email = _get("RESEND_FROM_EMAIL", "noreply@example.com")
        resend_from_name = _get("RESEND_FROM_NAME", "Mail Service")
        sender_email = _get("SENDER_EMAIL", resend_from_email)
        rate_limit_per_minute = int(_get("RATE_LIMIT_PER_MINUTE", "600"))
        max_retries = int(_get("MAX_RETRIES", "5"))
        concurrency = int(_get("CONCURRENCY", "10"))
        sqlite_db_path = _get("SQLITE_DB_PATH", "mailing.sqlite3")
        log_level = _get("LOG_LEVEL", "INFO")
        daily_email_limit = int(_get("DAILY_EMAIL_LIMIT", "100"))
        list_unsubscribe = _get("LIST_UNSUBSCRIBE", "")
        resend_webhook_secret = _get("RESEND_WEBHOOK_SECRET", "")

        return Settings(
            resend_api_key=resend_api_key,
            resend_base_url=resend_base_url,
            resend_from_email = resend_from_email,
            resend_from_name = resend_from_name,
            sender_email = sender_email,
            rate_limit_per_minute = rate_limit_per_minute,
            max_retries = max_retries,
            concurrency = concurrency,
            sqlite_db_path = sqlite_db_path,
            log_level = log_level,
            daily_email_limit = daily_email_limit,
            list_unsubscribe = list_unsubscribe or None,
            resend_webhook_secret = resend_webhook_secret or None,
        )


settings = Settings.load()
