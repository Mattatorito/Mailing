#!/usr/bin/env python3

from __future__ import annotations
import re
from typing import List, Optional, Tuple
from email.utils import parseaddr


class EmailValidator:
    """Валидатор email адресов."""
    
    # Базовый паттерн для email
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Более строгий паттерн
    STRICT_EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
    )
    
    def __init__(self, strict: bool = False):
        """Инициализирует валидатор.
        
        Args:
            strict: Использовать строгую валидацию
        """
        self.strict = strict
        self.pattern = self.STRICT_EMAIL_PATTERN if strict else self.EMAIL_PATTERN
    
    def is_valid(self, email: str) -> bool:
        """Проверяет валидность email адреса."""
        if not email or not isinstance(email, str):
            return False
        
        email = email.strip().lower()
        
        # Базовая проверка паттерном
        if not self.pattern.match(email):
            return False
        
        # Дополнительные проверки
        return self._additional_checks(email)
    
    def _additional_checks(self, email: str) -> bool:
        """Дополнительные проверки email."""
        
        # Проверяем длину
        if len(email) > 254:  # RFC 5321
            return False
        
        local, domain = email.rsplit('@', 1)
        
        # Проверяем длину локальной части
        if len(local) > 64:  # RFC 5321
            return False
        
        # Проверяем длину домена
        if len(domain) > 253:
            return False
        
        # Проверяем что нет последовательных точек
        if '..' in email:
            return False
        
        # Проверяем что не начинается и не заканчивается точкой
        if local.startswith('.') or local.endswith('.'):
            return False
        
        if domain.startswith('.') or domain.endswith('.'):
            return False
        
        return True
    
    def normalize(self, email: str) -> Optional[str]:
        """Нормализует email адрес."""
        if not self.is_valid(email):
            return None
        
        email = email.strip().lower()
        
        # Можно добавить дополнительную нормализацию
        # например, удаление точек из Gmail адресов
        
        return email
    
    def extract_domain(self, email: str) -> Optional[str]:
        """Извлекает домен из email адреса."""
        if not self.is_valid(email):
            return None
        
        return email.split('@')[1].lower()
    
    def validate_batch(self, emails: List[str]) -> List[Tuple[str, bool, Optional[str]]]:
        """Валидирует список email адресов.
        
        Returns:
            Список кортежей (email, is_valid, error_message)
        """
        results = []
        
        for email in emails:
            try:
                is_valid = self.is_valid(email)
                error = None if is_valid else "Invalid email format"
                results.append((email, is_valid, error))
            except Exception as e:
                results.append((email, False, str(e)))
        
        return results
    
    def get_typo_suggestions(self, email: str) -> List[str]:
        """Предлагает исправления для опечаток в email."""
        suggestions = []
        
        if '@' not in email:
            return suggestions
        
        local, domain = email.rsplit('@', 1)
        
        # Популярные домены для проверки опечаток
        popular_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'icloud.com', 'mail.ru', 'yandex.ru', 'rambler.ru'
        ]
        
        # Проверяем похожие домены
        for popular_domain in popular_domains:
            if self._is_similar_domain(domain, popular_domain):
                suggestion = f"{local}@{popular_domain}"
                if self.is_valid(suggestion):
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _is_similar_domain(self, domain1: str, domain2: str) -> bool:
        """Проверяет похожесть доменов."""
        # Простая проверка на опечатки
        if abs(len(domain1) - len(domain2)) > 2:
            return False
        
        # Считаем количество различий
        diff_count = sum(c1 != c2 for c1, c2 in zip(domain1, domain2))
        
        # Если различий мало относительно длины
        return diff_count <= max(1, len(domain2) // 4)


def validate_email(email: str, strict: bool = False) -> bool:
    """Простая функция для валидации email."""
    validator = EmailValidator(strict=strict)
    return validator.is_valid(email)


def normalize_email(email: str) -> Optional[str]:
    """Простая функция для нормализации email."""
    validator = EmailValidator()
    return validator.normalize(email)


def parse_email_with_name(email_string: str) -> Tuple[Optional[str], Optional[str]]:
    """Парсит строку с именем и email.
    
    Args:
        email_string: Строка вида "Name <email@domain.com>" или "email@domain.com"
    
    Returns:
        Кортеж (name, email)
    """
    try:
        name, email = parseaddr(email_string)
        
        # Проверяем что email валиден
        if email and validate_email(email):
            return (name.strip() if name else None, email.strip())
        
        return (None, None)
    except:
        return (None, None)


if __name__ == "__main__":
    # Тестирование валидатора
    validator = EmailValidator()
    
    test_emails = [
        "test@example.com",
        "invalid.email",
        "user@gmail.com",
        "bad@domain",
        "good.email@valid-domain.co.uk"
    ]
    
    for email in test_emails:
        is_valid = validator.is_valid(email)
        print(f"{email}: {'✅' if is_valid else '❌'}")
