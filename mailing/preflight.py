from __future__ import annotations
from typing import List, Tuple
import os

        import tempfile
        import uuid

from mailing.config import settings

def validate_env() -> List[str]:
    """Validate critical environment configuration; return list of error messages."""
    errors: List[str] = []
    if not settings.resend_api_key:errors.append("RESEND_API_KEY is missing")
    if not settings.resend_from_email:errors.append("RESEND_FROM_EMAIL is missing")if "@" not in settings.resend_from_email:errors.append("RESEND_FROM_EMAIL must be an email address")
    if not settings.resend_from_name:errors.append("RESEND_FROM_NAME is missing")

    # Rate limits sanity
    if settings.rate_limit_per_minute <= 0:errors.append("RATE_LIMIT_PER_MINUTE must be > 0")
    if settings.daily_email_limit <= 0:errors.append("DAILY_EMAIL_LIMIT must be > 0")
    if settings.concurrency <= 0:errors.append("CONCURRENCY must be > 0")

    # Database path check (directory must be writable)
    db_path = settings.sqlite_db_path
    try:db_dir = os.path.dirname(db_path) or "."

        # Создаем директорию если не существует
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, mode = 0o755, exist_ok = True)

        # Проверяем возможность записи через временный файл
test_filename = f".writetest_{uuid.uuid4().hex[:8]}"
        test_file = os.path.join(db_dir, test_filename)

        try:with open(test_file,"w", encoding="utf-8") as f:f.write("test_write_permissions")
        finally:
            # Убеждаемся что файл удален даже при ошибках
            try:
                if os.path.exists(test_file):
                    os.remove(test_file)
            except OSError:
                pass  # Файл может быть уже удален или недоступен

    except PermissionError as e:errors.append(f"Cannot write to DB directory ({db_path}): {e}")
    except OSError as e:errors.append(f"Cannot access DB directory for SQLITE_DB_PATH ({db_path}): {e}")
    except Exception as e:
        errors.append(f"Cannot write to DB directory for SQLITE_DB_PATH ({db_path}): {e}"
        )

    return errors

__all__ = ["validate_env"]
