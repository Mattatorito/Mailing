#!/usr/bin/env python3

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Recipient:
    """Класс для работы с получателем email."""
    
    email: str
    variables: Dict[str, Any] = None
    name: str = ""
    
    def __post_init__(self):
        """Инициализация после создания объекта."""
        if self.variables is None:
            self.variables = {}
        
        # Если имя не указано, пытаемся взять из переменных
        if not self.name and "name" in self.variables:
            self.name = str(self.variables["name"])


@dataclass 
class DeliveryResult:
    """Результат доставки email."""
    
    email: str
    success: bool
    status_code: int = 0
    message_id: str = ""
    error: str = ""
    provider: str = ""
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Инициализация после создания объекта."""
        if self.timestamp is None:
            from datetime import datetime
            self.timestamp = datetime.now().isoformat()
