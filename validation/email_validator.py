from __future__ import annotations
from email_validator import validate_email, EmailNotValidError
from typing import Iterable, List, Tuple


def validate_email_list(addresses: Iterable[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Возвращает (валидные, ошибки[(email, причина)])."""
    valid: List[str] = []
    errors: List[Tuple[str, str]] = []
    for addr in addresses:
        a = addr.strip()
        if not a:
            continue
        try:
            info = validate_email(a, check_deliverability=False)
            valid.append(info.normalized)
        except EmailNotValidError as e:
            errors.append((a, str(e)))
    return valid, errors
