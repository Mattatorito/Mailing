from __future__ import annotations
import orjson
from typing import List, Any, Dict
from .base import DataLoader
from mailing.models import Recipient

class JSONLoader(DataLoader):
    def load(self, path: str) -> List[Recipient]:
        with open(path, 'rb') as f:
            data = orjson.loads(f.read())
        recipients: List[Recipient] = []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict) or 'email' not in item:
                    continue
                email = str(item['email']).strip()
                variables = {k: v for k, v in item.items() if k != 'email'}
                recipients.append(self.build_recipient(email, variables))
        else:
            raise ValueError("JSON root must be a list of objects")
        return recipients
