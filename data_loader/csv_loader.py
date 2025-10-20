#!/usr/bin/env python3

from __future__ import annotations
import csv
import os
from typing import List, Dict, Any
from data_loader.base import DataLoader
from mailing.models import Recipient


class CSVLoader(DataLoader):
    """Загрузчик данных из CSV файлов."""
    
    def validate_source(self, source: str) -> bool:
        """Проверяет корректность CSV файла."""
        return os.path.exists(source) and source.endswith('.csv')
    
    def load(self, source: str) -> List[Recipient]:
        """Загружает получателей из CSV файла."""
        if not self.validate_source(source):
            raise ValueError(f"Некорректный CSV файл: {source}")
        
        recipients = []
        
        with open(source, 'r', encoding='utf-8') as csvfile:
            # Пытаемся определить диалект CSV
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)
            
            reader = csv.DictReader(csvfile, dialect=dialect)
            
            for row in reader:
                # Ищем колонку с email
                email_field = self._find_email_field(row)
                if not email_field:
                    continue
                
                email = row[email_field].strip()
                if not email:
                    continue
                
                recipient = self._create_recipient(email, row)
                recipients.append(recipient)
        
        return recipients
    
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
        
        return ""
