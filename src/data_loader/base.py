#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator
from src.mailing.models import Recipient


class DataLoader(ABC):
    """Базовый класс для загрузчиков данных."""
    
    @abstractmethod
    def load(self, source: str) -> List[Recipient]:
        """Загружает данные получателей из источника."""
        pass
    
    @abstractmethod 
    def validate_source(self, source: str) -> bool:
        """Проверяет корректность источника данных."""
        pass
    
    def _create_recipient(self, email: str, data: Dict[str, Any]) -> Recipient:
        """Создает объект получателя из данных."""
        name = data.get('name', data.get('Name', ''))
        variables = {k: v for k, v in data.items() if k.lower() not in ['email', 'name']}
        
        return Recipient(
            email=email,
            name=name,
            variables=variables
        )


class BaseDataLoader(DataLoader):
    """Базовая реализация загрузчика данных."""
    
    def load(self, source: str) -> List[Recipient]:
        """Базовая реализация - должна быть переопределена."""
        raise NotImplementedError("Subclasses must implement load method")
    
    def validate_source(self, source: str) -> bool:
        """Базовая валидация - проверяет что источник не пустой."""
        return bool(source)


class LoaderError(Exception):
    """Исключение для ошибок загрузки данных."""
    pass
