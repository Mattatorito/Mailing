#!/usr/bin/env python3

from __future__ import annotations
import csv
import os
from typing import List, Dict, Any
from pathlib import Path

from .base import BaseDataLoader, LoaderError
from src.mailing.models import Recipient

# Проверяем доступность email-validator
try:
    import email_validator
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False


class CSVLoader(BaseDataLoader):
    """Загрузчик данных из CSV файлов."""
    
    def validate_source(self, source: str) -> bool:
        """Проверяет корректность CSV файла."""
        return os.path.exists(source) and source.endswith('.csv')
    
    def _find_email_field(self, row: Dict[str, Any]) -> str:
        """Находит поле с email адресом."""
        email_candidates = ['email', 'Email', 'EMAIL', 'e-mail', 'E-mail']
        
        for field in email_candidates:
            if field in row and row[field]:
                return field
        
        # Если точного совпадения нет, ищем поле содержащее 'email'
        for field in row.keys():
            if 'email' in field.lower() and row[field]:
                return field
                
        # Специальная проверка для случаев когда CSV Sniffer обрезает название
        for field in row.keys():
            if field and field.lower().startswith('emai') and row[field]:
                return field
        
        return ""
    
    def load(self, source: str, delimiter: str = None, validate_emails: bool = False) -> List[Recipient]:
        """Загружает получателей из CSV файла с дополнительными параметрами."""
        if not os.path.exists(source):
            raise LoaderError(f"Файл не найден: {source}")
        
        recipients = []
        
        try:
            with open(source, 'r', encoding='utf-8') as csvfile:
                # Используем указанный разделитель или автоопределение
                reader = None
                if delimiter:
                    reader = csv.DictReader(csvfile, delimiter=delimiter)
                else:
                    # Сначала пробуем с запятой по умолчанию
                    reader = csv.DictReader(csvfile)
                    
                    # Проверяем есть ли email поле
                    if reader.fieldnames:
                        headers_dict = {field: field for field in reader.fieldnames if field}
                        if not self._find_email_field(headers_dict):
                            # Если email поле не найдено, пробуем автоопределение диалекта
                            sample = csvfile.read(1024)
                            csvfile.seek(0)
                            if sample:
                                try:
                                    dialect = csv.Sniffer().sniff(sample)
                                    reader = csv.DictReader(csvfile, dialect=dialect)
                                except csv.Error:
                                    # Возвращаемся к default reader
                                    csvfile.seek(0)
                                    reader = csv.DictReader(csvfile)
                
                # Проверяем наличие колонки email
                if reader.fieldnames is None:
                    return []
                
                # Создаем словарь для поиска email поля
                headers_dict = {field: field for field in reader.fieldnames if field}
                email_field = self._find_email_field(headers_dict)
                if not email_field:
                    raise LoaderError("CSV файл не содержит колонку с email адресами")
                
                for row in reader:
                    email = row.get(email_field, '').strip()
                    if not email:
                        continue
                    
                    # Валидация email если требуется
                    if validate_emails and EMAIL_VALIDATOR_AVAILABLE:
                        try:
                            email_validator.validate_email(email)
                        except email_validator.EmailNotValidError:
                            continue  # Пропускаем невалидные email
                    
                    recipient = self._create_recipient(email, row, email_field)
                    recipients.append(recipient)
                    
        except Exception as e:
            raise LoaderError(f"Ошибка при загрузке CSV файла: {e}")
        
        return recipients

    def _create_recipient(self, email: str, row: Dict[str, Any], email_field: str) -> Recipient:
        """Создает объект Recipient из данных строки."""
        # Убираем email из переменных
        variables = {k: v for k, v in row.items() if k != email_field and v}
        
        # Получаем имя из колонки name или используем email
        name = row.get('name') or row.get('Name') or row.get('NAME') or email
        
        return Recipient(
            email=email,
            name=name,
            variables=variables
        )
