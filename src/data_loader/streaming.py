#!/usr/bin/env python3

from __future__ import annotations
import csv
from typing import Iterator, Dict, Any
from src.data_loader.csv_loader import CSVLoader
from src.data_loader.base import LoaderError
from src.mailing.models import Recipient


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
                
                recipient = self._create_recipient(email, row, email_field)
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


class StreamingDataLoader:
    """Универсальный потоковый загрузчик данных."""
    
    def stream(self, data_source: Iterator[Dict[str, Any]]) -> Iterator[Recipient]:
        """Обрабатывает поток данных и возвращает получателей."""
        for item in data_source:
            if not isinstance(item, dict) or 'email' not in item:
                continue  # Пропускаем невалидные записи
            
            email = item.get('email', '').strip()
            if not email:
                continue
            
            name = item.get('name', email)  # Используем email как имя если name отсутствует
            variables = {k: v for k, v in item.items() if k not in ['email', 'name']}
            
            yield Recipient(email=email, name=name, variables=variables)
    
    def batch_stream(self, data_source: Iterator[Dict[str, Any]], batch_size: int = 100) -> Iterator[list[Recipient]]:
        """Обрабатывает поток данных батчами."""
        batch = []
        
        for recipient in self.stream(data_source):
            batch.append(recipient)
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # Отдаем последний батч если он не пустой
        if batch:
            yield batch
