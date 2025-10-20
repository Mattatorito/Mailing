from __future__ import annotations
from typing import Iterable, List, Tuple

from email_validator import validate_email, EmailNotValidError


class EmailValidator:
    """Валидатор email адресов."""
    
    def is_valid(self, email: str) -> bool:
        """Проверяет валидность email адреса.
        
        Args:
            email: Email адрес для проверки
            
        Returns:
            bool: True если email валиден, False иначе
        """
        try:
            validate_email(email, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False


def validate_email_list(
    addresses: Iterable[str],
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Выполняет validate email list.
    
    Возвращает (валидные, ошибки[(email, причина)]).
    """
    valid: List[str] = []
    errors: List[Tuple[str, str]] = []
    for addr in addresses:
        a = addr.strip()
        if not a:
            continue
        try:
            info = validate_email(a, check_deliverability = False)
            valid.append(info.normalized)
        except EmailNotValidError as e:
            errors.append((a, str(e)))
    return valid, errors
