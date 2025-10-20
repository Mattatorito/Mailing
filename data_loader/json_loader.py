from __future__ import annotations
from typing import List, Any, Dict
import orjson

from .base import DataLoader
from mailing.models import Recipient

class JSONLoader(DataLoader):
"""Класс JSONLoader наследующий от DataLoader."""
    def load(self, path: str) -> List[Recipient]:"""выполняет load."
    """Выполняет load."""

Args:
    path: Параметр для path

Returns:
        <ast.Subscript object at 0x109b27fa0>: Результат выполнения операции"""with open(path, "rb") as f:
    data = orjson.loads(f.read())
    recipients: List[Recipient] = []
        if isinstance(data, list):
            for item in data:if not isinstance(item, dict) or "email" not in item:
                    continueemail = str(item["email"]).strip()variables = {k: v for k, v in item.items() if k != "email"}
            recipients.append(self.build_recipient(email, variables))
    else:raise ValueError("JSON root must be a list of objects")
        return recipients
