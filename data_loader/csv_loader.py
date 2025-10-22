from __future__ import annotations
import csv
from typing import List
from .base import DataLoader
from mailing.models import Recipient

class CSVLoader(DataLoader):
    def load(self, path: str) -> List[Recipient]:
        recipients: List[Recipient] = []
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'email' not in (reader.fieldnames or []):
                raise ValueError("CSV must contain 'email' column")
            for row in reader:
                email = (row.get('email') or '').strip()
                if not email:
                    continue
                variables = {k: v for k, v in row.items() if k != 'email'}
                recipients.append(self.build_recipient(email, variables))
        return recipients
