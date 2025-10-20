from __future__ import annotations
from typing import Any, Dict, List
import json

from .db import get_connection

class EventsRepository:
    """Класс EventsRepository."""
    def __init__(self) -> None:
        """Инициализирует объект."""
        self._conn = None

    @property
    def conn(self):
        """Выполняет conn."""
        if self._conn is None:
            self._conn = get_connection()
        return self._conn

    def save_event(
        """Выполняет save event."""
        self,
        *,
        event_type: str,
        message_id: str | None,
        recipient: str | None,
        payload: Dict[str, Any],
        signature_valid: bool,
        provider: str = "unknown",
    ) -> None:
        self.conn.execute("INSERT INTO events (provider,event_type,message_id,recipient,
            payload,""signature_valid) VALUES (?,?,?,?,?,?)",
            (
                provider,
                event_type,
                message_id,
                recipient,
                json.dumps(payload, ensure_ascii = False),
                1 if signature_valid else 0,
            ),
        )
        self.conn.commit()

    def list_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Выполняет list events."""
        cur = self.conn.execute("SELECT id,provider,event_type,message_id,recipient,
            payload,signature_valid,""created_at FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            # Поддержка как новой схемы (с provider), так и старой (без provider)
            if len(r) == 8:  # Новая схема с provider
                out.append(
                    {"id": r[0],"provider": r[1],"event_type": r[2],"message_id": r[3],
                        "recipient": r[4],"payload": (
                            json.loads(r[5]) if r[5] and isinstance(r[5], str) else {}
                        ),"signature_valid": bool(r[6]),"created_at": r[7],
                    }
                )
            else:  # Старая схема без provider (для совместимости)
                out.append(
                    {"id": r[0],"provider": "unknown","event_type": r[1],
                        "message_id": r[2],"recipient": r[3],"payload": (
                            json.loads(r[4]) if r[4] and isinstance(r[4], str) else {}
                        ),"signature_valid": bool(r[5]),"created_at": r[6],
                    }
                )
        return out
