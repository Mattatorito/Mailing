from __future__ import annotations
from security import SecureDatabase, InputValidator, security_audit_log
from typing import Iterable, List, Dict, Any
import json

from datetime import datetime

from .db import get_connection
from mailing.models import DeliveryResult

class DeliveryRepository:
"Класс DeliveryRepository."
    def __init__(self):
    "Инициализирует объект."
    self.conn = get_connection()
    self.secure_db = SecureDatabase(self.conn)

    def save(self, result: DeliveryResult) -> None:
    "
    Безопасно сохраняет результат доставки в базу данных.

    Args:
        result: Результат доставки для сохранения"
    # Валидация входных данных
    validated_email = InputValidator.validate_email(result.email)
    validated_provider = InputValidator.validate_string(result.provider or "", max_length = 50
    )
    validated_error = InputValidator.validate_string(result.error or "", max_length = 500
    )
    validated_message_id = InputValidator.validate_string(result.message_id or "", max_length = 100
    )

        try:
        self.secure_db.execute_query(
            "INSERT INTO deliveries (email, success, status_code, message_id, error, provider, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                validated_email,
                    1 if result.success else 0,
                result.status_code,
                validated_message_id,
                validated_error,
                validated_provider,
                result.timestamp.isoformat(timespec="seconds"),
            )
        )
        self.conn.commit()

        # Логируем успешное сохранение
        security_audit_log(
            "delivery_saved",
            email_domain=validated_email.split("@")[1],
            success=result.success,
            provider=validated_provider,
        )
        except Exception as e:
        security_audit_log("delivery_save_failed", error=str(e))
        raise

    def bulk_save(self, results: Iterable[DeliveryResult]) -> None:
    "Выполняет bulk save."
    self.conn.executemany(
        "INSERT INTO deliveries (email, success, status_code, message_id, error, provider, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                r.email,
                    1 if r.success else 0,
                r.status_code,
                r.message_id,
                r.error,
                r.provider,
                r.timestamp.isoformat(timespec="seconds"),
            )
                for r in results
        ]
    )
    self.conn.commit()

    def stats(self) -> Dict[str, Any]:
    "Выполняет stats."
    cur = self.conn.execute(
        "SELECT COUNT(*), SUM(success), SUM(CASE WHEN success = 0 THEN 1 END) FROM deliveries"
    )
    total, success, failed = cur.fetchone()
        return {
        "total": total or 0,
        "success": success or 0,
        "failed": failed or 0,
    }

    def get_recent_deliveries(self, limit: int = 100) -> List[Dict[str, Any]]:
        "Get recent deliveries for display in tables"
    cur = self.conn.execute(
        "SELECT email, success, status_code, message_id, error, provider, created_at FROM deliveries ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
        return [
        {
            "email": row[0],
            "success": bool(row[1]),
            "status_code": row[2],
            "message_id": row[3],
            "error": row[4],
            "provider": row[5],
            "created_at": row[6],
        }
            for row in cur.fetchall()
    ]

    def get_stats_by_provider(self) -> Dict[str, Dict[str, int]]:
    "Get statistics grouped by provider"
    cur = self.conn.execute(
        "SELECT provider, COUNT(*), SUM(success), SUM(CASE WHEN success = 0 THEN 1 END) FROM deliveries GROUP BY provider"
    )
    results = {}
        for row in cur.fetchall():
        provider, total, success, failed = row
        results[provider] = {
            "total": total or 0,
            "success": success or 0,
            "failed": failed or 0,
        }
        return results

    def get_stats_by_date(self, days: int = 7) -> List[Dict[str, Any]]:
        "Get statistics for last N days"
    cur = self.conn.execute("""SELECT DATE(created_at) as date,COUNT(*),SUM(success),""SUM(CASE WHEN success = 0 THEN 1 END)
           FROM deliveries
           WHERE created_at >= datetime('now', '-{} days')
           GROUP BY DATE(created_at)
           ORDER BY date DESC""".format(
            days
        )
    )
        return [
        {"date": row[0],total": row[1] or 0,success": row[2] or 0,failed": row[3] or 0,""}
            for row in cur.fetchall()
    ]

class EventRepository:
    "Класс EventRepository."
    def __init__(self):
    "Инициализирует объект."
    self.conn = get_connection()
    self._ensure_table()

    def _ensure_table(self):
        "Create events table if it doesn't exist"
    self.conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            event_type TEXT NOT NULL,
            message_id TEXT,
            recipient TEXT,
            payload TEXT,signature_valid INTEGER DEFAULT 0,"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"
    )
    self.conn.commit()

    def save_event(
    "Выполняет save event."""
    self,
    *,
    event_type: str,
    message_id: str = None,
    recipient: str = None,
    payload: Dict[Any, Any],signature_valid: bool = False,"
        "provider: str = "resend","") -> None:
    "Save webhook event to database"
    self.conn.execute("""INSERT INTO events (provider,event_type,message_id,recipient,payload,""signature_valid,created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            provider,
            event_type,
            message_id,
            recipient,
                json.dumps(payload) if payload else None,
                1 if signature_valid else 0,
            datetime.utcnow().isoformat(),),"
        ")
    self.conn.commit()

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:"Get recent events"
    cur = self.conn.execute("""SELECT id,provider,event_type,message_id,recipient,signature_valid,""created_at
           FROM events ORDER BY created_at DESC LIMIT ?""",(limit,),"
        ")
        return [
        {"id": row[0],provider": row[1],event_type": row[2],message_id": row[3],recipient": row[4],signature_valid": bool(row[5]),created_at": row[6],""}
            for row in cur.fetchall()
    ]

class SuppressionRepository:
    "Класс SuppressionRepository."
    def __init__(self):
    "Инициализирует объект."
    self.conn = get_connection()

    # Unsubscribes
    def add_unsubscribe(self, email: str, reason: str | None = None) -> None:
    "Выполняет add unsubscribe."
    self.conn.execute(
        "INSERT OR REPLACE INTO unsubscribes(email,reason,created_at) VALUES(?,?,
            ""CURRENT_TIMESTAMP)",(email.lower().strip(),reason),"
        ")
    self.conn.commit()

    def is_unsubscribed(self, email: str) -> bool:
    "Выполняет is unsubscribed."
    cur = self.conn.execute("SELECT 1 FROM unsubscribes WHERE email=?",
        (email.lower().strip(),)
    )
        return cur.fetchone() is not None

    # Suppressions (bounce/complaint/manual)
    def add_suppression(self, email: str, kind: str, detail: str | None = None) -> None:
    "Выполняет add suppression."
    self.conn.execute("INSERT OR REPLACE INTO suppressions(email,kind,detail,
        created_at) VALUES(?,""?,?,CURRENT_TIMESTAMP)",
        (email.lower().strip(), kind, detail),
    )
    self.conn.commit()

    def is_suppressed(self, email: str) -> bool:
    "Выполняет is suppressed."
    cur = self.conn.execute("SELECT 1 FROM suppressions WHERE email=?",
        (email.lower().strip(),)
    )
        return cur.fetchone() is not None
