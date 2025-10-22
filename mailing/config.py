from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

@dataclass(frozen=True)
class Settings:
    # Resend configuration (primary and only provider)
    resend_api_key: str
    resend_base_url: str
    resend_from_email: str
    resend_from_name: str
    
    # Application settings
    sender_email: str
    rate_limit_per_minute: int
    max_retries: int
    concurrency: int
    sqlite_db_path: str
    log_level: str
    daily_email_limit: int

    @staticmethod
    def load() -> "Settings":
        def _get(name: str, default: Optional[str] = None, required: bool = False) -> str:
            val = os.getenv(name, default)
            if required and (val is None or val == ""):
                raise RuntimeError(f"Missing required environment variable: {name}")
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

        return Settings(
            resend_api_key=resend_api_key,
            resend_base_url=resend_base_url,
            resend_from_email=resend_from_email,
            resend_from_name=resend_from_name,
            sender_email=sender_email,
            rate_limit_per_minute=rate_limit_per_minute,
            max_retries=max_retries,
            concurrency=concurrency,
            sqlite_db_path=sqlite_db_path,
            log_level=log_level,
            daily_email_limit=daily_email_limit,
        )

settings = Settings.load()
