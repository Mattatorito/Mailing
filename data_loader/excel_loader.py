#!/usr/bin/env python3

from __future__ import annotations
import os
from typing import List, Dict, Any
from data_loader.base import DataLoader
from mailing.models import Recipient

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class ExcelLoader(DataLoader):
    """Загрузчик данных из Excel файлов."""
    
    def validate_source(self, source: str) -> bool:
        """Проверяет корректность Excel файла."""
        if not PANDAS_AVAILABLE:
            return False
        
        return (os.path.exists(source) and 
                source.endswith(('.xlsx', '.xls', '.xlsm')))
    
    def load(self, source: str) -> List[Recipient]:
        """Загружает получателей из Excel файла."""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas не установлен. Установите: pip install pandas openpyxl")
        
        if not self.validate_source(source):
            raise ValueError(f"Некорректный Excel файл: {source}")
        
        recipients = []
        
        # Читаем Excel файл
        df = pd.read_excel(source)
        
        # Ищем колонку с email
        email_column = self._find_email_column(df.columns)
        if not email_column:
            raise ValueError("Не найдена колонка с email адресами")
        
        for _, row in df.iterrows():
            email = str(row[email_column]).strip()
            if not email or email == 'nan':
                continue
            
            # Преобразуем строку в словарь
            row_data = row.to_dict()
            recipient = self._create_recipient(email, row_data)
            recipients.append(recipient)
        
        return recipients
    
    def _find_email_column(self, columns) -> str:
        """Находит колонку с email адресами."""
        email_candidates = ['email', 'Email', 'EMAIL', 'e-mail', 'E-mail']
        
        for candidate in email_candidates:
            if candidate in columns:
                return candidate
        
        # Ищем колонку содержащую 'email' в названии
        for col in columns:
            if 'email' in str(col).lower():
                return col
        
        return ""
