#!/usr/bin/env python3

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import html
import re


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
        
        # Санитизация имени получателя
        if self.name:
            self.name = self._sanitize_string(self.name)
        
        # Санитизация переменных
        if self.variables:
            self.variables = self._sanitize_variables(self.variables)
        
        # Если имя не указано, используем email как имя
        if not self.name:
            if "name" in self.variables:
                self.name = str(self.variables["name"])
            else:
                self.name = self.email
    
    def _sanitize_string(self, value: str) -> str:
        """Санитизация строковых значений."""
        if not isinstance(value, str):
            return str(value)
        
        # Удаляем опасные символы и паттерны
        dangerous_patterns = [
            r'<script.*?</script>',
            r'<iframe.*?</iframe>',
            r'javascript:',
            r'<.*?>',  # Все HTML теги
            r'\x00',   # Null bytes
            r'\r\n',   # CRLF injection
            r'\n',     # Newline injection
        ]
        
        sanitized = value
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Ограничиваем длину для предотвращения DoS
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
        
        # Экранируем HTML
        sanitized = html.escape(sanitized)
        
        return sanitized
    
    def _sanitize_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Санитизация словаря переменных."""
        sanitized = {}
        
        for key, value in variables.items():
            # Санитизация ключа
            clean_key = self._sanitize_string(str(key))
            
            # Санитизация значения
            if isinstance(value, str):
                clean_value = self._sanitize_string(value)
            elif isinstance(value, (int, float, bool)):
                clean_value = value
            elif isinstance(value, dict):
                clean_value = self._sanitize_variables(value)
            elif isinstance(value, list):
                clean_value = [self._sanitize_string(str(item)) if isinstance(item, str) else item for item in value]
            else:
                clean_value = self._sanitize_string(str(value))
            
            sanitized[clean_key] = clean_value
        
        return sanitized


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
