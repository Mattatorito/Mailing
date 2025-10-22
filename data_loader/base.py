from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Dict, Any, List
from mailing.models import Recipient

class DataLoader(ABC):
    @abstractmethod
    def load(self, path: str) -> List[Recipient]:
        ...

    @staticmethod
    def build_recipient(email: str, variables: Dict[str, Any]) -> Recipient:
        return Recipient(email=email, variables=variables)
