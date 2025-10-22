#!/usr/bin/env python3

from __future__ import annotations
import os
from typing import List, Dict, Any

from .base import BaseDataLoader, LoaderError
from src.mailing.models import Recipient

# Проверяем доступность openpyxl
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class ExcelLoader(BaseDataLoader):
    """Загрузчик данных из Excel файлов."""
    
    def validate_source(self, source: str) -> bool:
        """Проверяет корректность Excel файла."""
        if not OPENPYXL_AVAILABLE:
            return False
        
        return (os.path.exists(source) and 
                source.endswith(('.xlsx', '.xls', '.xlsm')))
    
    def load(self, source: str) -> List[Recipient]:
        """Загружает получателей из Excel файла."""
        if not OPENPYXL_AVAILABLE:
            raise LoaderError("openpyxl не установлен. Установите: pip install openpyxl")
        
        if not os.path.exists(source):
            raise LoaderError(f"Файл не найден: {source}")
        
        try:
            workbook = openpyxl.load_workbook(source)
            worksheet = workbook.active
            
            # Получаем заголовки из первой строки
            headers = []
            for cell in worksheet[1]:
                headers.append(cell.value)
            
            # Ищем колонку с email
            email_col_index = self._find_email_column(headers)
            if email_col_index is None:
                raise LoaderError("Excel файл не содержит колонку с email адресами")
            
            recipients = []
            
            # Обрабатываем строки начиная со второй
            for row in worksheet.iter_rows(min_row=2, values_only=True):
                if not row or len(row) <= email_col_index:
                    continue
                
                email = str(row[email_col_index]).strip() if row[email_col_index] else ""
                if not email:
                    continue
                
                # Создаем словарь данных строки
                row_data = {}
                for i, header in enumerate(headers):
                    if i < len(row) and header:
                        row_data[header] = row[i]
                
                recipient = self._create_recipient(email, row_data)
                recipients.append(recipient)
                
            return recipients
            
        except Exception as e:
            raise LoaderError(f"Ошибка при загрузке Excel файла: {e}")

    def _find_email_column(self, headers) -> int:
        """Находит индекс колонки с email."""
        email_candidates = ['email', 'Email', 'EMAIL', 'e-mail', 'E-mail']
        
        for i, header in enumerate(headers):
            if header in email_candidates:
                return i
        
        # Поиск по содержимому
        for i, header in enumerate(headers):
            if header and 'email' in str(header).lower():
                return i
        
        return None

    def _create_recipient(self, email: str, row_data: Dict[str, Any]) -> Recipient:
        """Создает объект Recipient из данных строки."""
        # Убираем email из переменных
        variables = {k: v for k, v in row_data.items() if k != 'email' and v is not None}
        
        # Получаем имя из колонки name или используем email
        name = row_data.get('name') or row_data.get('Name') or row_data.get('NAME') or email
        
        return Recipient(
            email=email,
            name=name,
            variables=variables
        )
