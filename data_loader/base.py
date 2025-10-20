from __future__ import annotations
from typing import Iterable, Dict, Any, List

from abc import ABC, abstractmethod

from mailing.models import Recipient

class DataLoader(ABC):
    """Класс DataLoader наследующий от ABC."""
    @abstractmethod
    def load(self, path: str) -> List[Recipient]:
        """Выполняет load.

        Args:
            path: Параметр для path

        Returns:
            List[Recipient]: Результат выполнения операции
        """
        ...

    @staticmethod
    def build_recipient(email: str, variables: Dict[str, Any]) -> Recipient:
        """Выполняет build recipient.

        Args:
            email: Параметр для email
            variables: Параметр для variables

        Returns:
            Recipient: Результат выполнения операции
        """
        # Извлекаем name из variables если есть
        name = variables.get("name")
        # Фильтруем только строковые ключи для **kwargs
        other_vars = {k: v for k, v in variables.items() if k != "name" and isinstance(k, str)}
        return Recipient(email=email, name=name, **other_vars)
