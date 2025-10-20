#!/usr/bin/env python3

from __future__ import annotations
import csv
from typing import Iterator, Dict, Any
from data_loader.csv_loader import CSVLoader
from mailing.models import Recipient


class StreamingCSVLoader(CSVLoader):
    """Потоковый загрузчик CSV для больших файлов."""
    
    def __init__(self, chunk_size: int = 1000):
        """Инициализирует потоковый загрузчик."""
        self.chunk_size = chunk_size
    
    def load_stream(self, source: str) -> Iterator[Recipient]:
        """Загружает получателей потоком для экономии памяти."""
        if not self.validate_source(source):
            raise ValueError(f"Некорректный CSV файл: {source}")
        
        with open(source, 'r', encoding='utf-8') as csvfile:
            # Определяем диалект CSV
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
                yield recipient
    
    def load_chunks(self, source: str) -> Iterator[list[Recipient]]:
        """Загружает получателей порциями."""
        chunk = []
        
        for recipient in self.load_stream(source):
            chunk.append(recipient)
            
            if len(chunk) >= self.chunk_size:
                yield chunk
                chunk = []
        
        # Отдаем последнюю порцию если она не пустая
        if chunk:
            yield chunk
