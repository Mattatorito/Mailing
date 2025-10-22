from __future__ import annotations
import json
from typing import Any, Dict, List
from .db import get_connection

class EventsRepository:
    def __init__(self) -> None:
        self.conn = get_connection()

    def save_event(self, *, event_type: str, message_id: str | None, recipient: str | None, payload: Dict[str, Any], signature_valid: bool) -> None:
        self.conn.execute(
            "INSERT INTO events (event_type, message_id, recipient, payload_json, signature_valid) VALUES (?,?,?,?,?)",
            (
                event_type,
                message_id,
                recipient,
                json.dumps(payload, ensure_ascii=False),
                1 if signature_valid else 0,
            ),
        )
        self.conn.commit()

    def list_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            "SELECT id, event_type, message_id, recipient, payload_json, signature_valid, created_at FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "id": r[0],
                    "event_type": r[1],
                    "message_id": r[2],
                    "recipient": r[3],
                    "payload": json.loads(r[4]),
                    "signature_valid": bool(r[5]),
                    "created_at": r[6],
                }
            )
        return out
