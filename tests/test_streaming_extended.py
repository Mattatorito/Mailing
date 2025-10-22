#!/usr/bin/env python3
"""
Comprehensive tests for data_loader/streaming.py
"""

import pytest
import csv
import tempfile
from pathlib import Path
from typing import Iterator, Dict, Any
from unittest.mock import Mock, patch, mock_open

from src.data_loader.streaming import StreamingCSVLoader, StreamingDataLoader
from src.data_loader.base import LoaderError
from src.mailing.models import Recipient


class TestStreamingCSVLoader:
    """Тесты для StreamingCSVLoader."""
    
    @pytest.fixture
    def loader(self):
        """Фикстура загрузчика."""
        return StreamingCSVLoader(chunk_size=3)
    
    @pytest.fixture
    def sample_csv_file(self):
        """Фикстура с временным CSV файлом."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['email', 'name', 'age', 'city'])
            writer.writerow(['alice@example.com', 'Alice Smith', '25', 'New York'])
            writer.writerow(['bob@example.com', 'Bob Johnson', '30', 'Boston'])
            writer.writerow(['charlie@example.com', 'Charlie Brown', '35', 'Chicago'])
            writer.writerow(['diana@example.com', 'Diana Wilson', '28', 'Denver'])
            writer.writerow(['eve@example.com', 'Eve Davis', '32', 'Seattle'])
            temp_file = f.name
        
        yield temp_file
        Path(temp_file).unlink(missing_ok=True)
    
    @pytest.fixture
    def sample_csv_semicolon(self):
        """Фикстура с CSV файлом с точкой с запятой."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write('email;name;department\n')
            f.write('test1@example.com;John Doe;Engineering\n')
            f.write('test2@example.com;Jane Smith;Marketing\n')
            temp_file = f.name
        
        yield temp_file
        Path(temp_file).unlink(missing_ok=True)
    
    @pytest.fixture
    def csv_with_empty_rows(self):
        """Фикстура с CSV файлом содержащим пустые строки."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['email', 'name'])
            writer.writerow(['valid@example.com', 'Valid User'])
            writer.writerow(['', 'Empty Email'])  # Пустой email
            writer.writerow(['  ', 'Whitespace Email'])  # Только пробелы
            writer.writerow(['another@example.com', 'Another User'])
            temp_file = f.name
        
        yield temp_file
        Path(temp_file).unlink(missing_ok=True)
    
    def test_init_default_chunk_size(self):
        """Тест инициализации с размером порции по умолчанию."""
        loader = StreamingCSVLoader()
        assert loader.chunk_size == 1000
    
    def test_init_custom_chunk_size(self):
        """Тест инициализации с кастомным размером порции."""
        loader = StreamingCSVLoader(chunk_size=500)
        assert loader.chunk_size == 500
    
    def test_load_stream_basic(self, loader, sample_csv_file):
        """Тест базовой потоковой загрузки."""
        recipients = list(loader.load_stream(sample_csv_file))
        
        assert len(recipients) == 5
        assert all(isinstance(r, Recipient) for r in recipients)
        assert recipients[0].email == 'alice@example.com'
        assert recipients[0].name == 'Alice Smith'
        assert recipients[1].email == 'bob@example.com'
        assert recipients[4].email == 'eve@example.com'
    
    def test_load_stream_invalid_file(self, loader):
        """Тест обработки несуществующего файла."""
        with pytest.raises(ValueError, match="Некорректный CSV файл"):
            list(loader.load_stream('nonexistent.csv'))
    
    def test_load_stream_dialect_detection(self, loader, sample_csv_semicolon):
        """Тест автоматического определения диалекта CSV."""
        recipients = list(loader.load_stream(sample_csv_semicolon))
        
        assert len(recipients) == 2
        assert recipients[0].email == 'test1@example.com'
        assert recipients[0].name == 'John Doe'
        assert recipients[1].email == 'test2@example.com'
    
    def test_load_stream_empty_emails(self, loader, csv_with_empty_rows):
        """Тест обработки пустых email адресов."""
        recipients = list(loader.load_stream(csv_with_empty_rows))
        
        # Должны загрузиться только записи с валидными email
        assert len(recipients) == 2
        assert recipients[0].email == 'valid@example.com'
        assert recipients[1].email == 'another@example.com'
    
    def test_load_chunks_basic(self, loader, sample_csv_file):
        """Тест загрузки порциями."""
        chunks = list(loader.load_chunks(sample_csv_file))
        
        # С chunk_size=3 должно быть 2 порции: [3, 2]
        assert len(chunks) == 2
        assert len(chunks[0]) == 3
        assert len(chunks[1]) == 2
        
        # Проверяем что все получатели на месте
        all_recipients = [r for chunk in chunks for r in chunk]
        assert len(all_recipients) == 5
        assert all_recipients[0].email == 'alice@example.com'
        assert all_recipients[4].email == 'eve@example.com'
    
    def test_load_chunks_exact_division(self):
        """Тест когда количество записей точно делится на размер порции."""
        loader = StreamingCSVLoader(chunk_size=2)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['email', 'name'])
            writer.writerow(['user1@example.com', 'User 1'])
            writer.writerow(['user2@example.com', 'User 2'])
            writer.writerow(['user3@example.com', 'User 3'])
            writer.writerow(['user4@example.com', 'User 4'])
            temp_file = f.name
        
        try:
            chunks = list(loader.load_chunks(temp_file))
            assert len(chunks) == 2
            assert len(chunks[0]) == 2
            assert len(chunks[1]) == 2
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def test_load_chunks_empty_file(self, loader):
        """Тест загрузки пустого CSV файла."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['email', 'name'])  # Только заголовок
            temp_file = f.name
        
        try:
            chunks = list(loader.load_chunks(temp_file))
            assert len(chunks) == 0
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def test_load_chunks_single_record(self, loader):
        """Тест загрузки файла с одной записью."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['email', 'name'])
            writer.writerow(['single@example.com', 'Single User'])
            temp_file = f.name
        
        try:
            chunks = list(loader.load_chunks(temp_file))
            assert len(chunks) == 1
            assert len(chunks[0]) == 1
            assert chunks[0][0].email == 'single@example.com'
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def test_inheritance_from_csv_loader(self, loader):
        """Тест что StreamingCSVLoader наследует от CSVLoader."""
        from src.data_loader.csv_loader import CSVLoader
        assert isinstance(loader, CSVLoader)
    
    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_load_stream_file_error(self, mock_file, loader):
        """Тест обработки ошибки открытия файла."""
        with patch.object(loader, 'validate_source', return_value=True):
            with pytest.raises(FileNotFoundError):
                list(loader.load_stream('missing.csv'))
    
    def test_csv_sniffer_error_handling(self, loader):
        """Тест обработки ошибок CSV Sniffer."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write('invalid,csv,without,proper,structure\n')
            f.write('no consistent delimiters here\n')
            temp_file = f.name
        
        try:
            # Даже с нестандартным форматом должно работать
            recipients = list(loader.load_stream(temp_file))
            # Может не найти email поля, поэтому список может быть пустым
            assert isinstance(recipients, list)
        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestStreamingDataLoader:
    """Расширенные тесты для StreamingDataLoader."""
    
    @pytest.fixture
    def loader(self):
        """Фикстура загрузчика."""
        return StreamingDataLoader()
    
    def test_stream_basic_functionality(self, loader):
        """Тест базовой функциональности потока."""
        def data_source():
            yield {"email": "user1@example.com", "name": "User 1", "age": 25}
            yield {"email": "user2@example.com", "name": "User 2", "age": 30}
        
        recipients = list(loader.stream(data_source()))
        
        assert len(recipients) == 2
        assert recipients[0].email == "user1@example.com"
        assert recipients[0].name == "User 1"
        assert recipients[0].variables == {"age": 25}
        assert recipients[1].variables == {"age": 30}
    
    def test_stream_email_as_name_fallback(self, loader):
        """Тест использования email как имени если name отсутствует."""
        def data_source():
            yield {"email": "test@example.com", "city": "New York"}
        
        recipients = list(loader.stream(data_source()))
        
        assert len(recipients) == 1
        assert recipients[0].email == "test@example.com"
        assert recipients[0].name == "test@example.com"  # Fallback
        assert recipients[0].variables == {"city": "New York"}
    
    def test_stream_skip_invalid_items(self, loader):
        """Тест пропуска невалидных элементов."""
        def data_source():
            yield {"email": "valid@example.com", "name": "Valid"}
            yield "invalid_string"  # Не словарь
            yield {"name": "No Email"}  # Нет email
            yield {"email": "", "name": "Empty Email"}  # Пустой email
            yield {"email": "  ", "name": "Whitespace Email"}  # Только пробелы
            yield {"email": "another@example.com", "name": "Another"}
        
        recipients = list(loader.stream(data_source()))
        
        assert len(recipients) == 2
        assert recipients[0].email == "valid@example.com"
        assert recipients[1].email == "another@example.com"
    
    def test_stream_variables_extraction(self, loader):
        """Тест извлечения переменных."""
        def data_source():
            yield {
                "email": "test@example.com",
                "name": "Test User",
                "company": "Test Corp",
                "department": "Engineering",
                "location": "Remote"
            }
        
        recipients = list(loader.stream(data_source()))
        
        assert len(recipients) == 1
        recipient = recipients[0]
        assert recipient.email == "test@example.com"
        assert recipient.name == "Test User"
        assert recipient.variables == {
            "company": "Test Corp",
            "department": "Engineering",
            "location": "Remote"
        }
    
    def test_stream_empty_data_source(self, loader):
        """Тест пустого источника данных."""
        def empty_data_source():
            return
            yield  # Unreachable
        
        recipients = list(loader.stream(empty_data_source()))
        assert len(recipients) == 0
    
    def test_batch_stream_basic(self, loader):
        """Тест базовой пакетной обработки."""
        def data_source():
            for i in range(7):
                yield {"email": f"user{i}@example.com", "name": f"User {i}"}
        
        batches = list(loader.batch_stream(data_source(), batch_size=3))
        
        assert len(batches) == 3  # [3, 3, 1]
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3
        assert len(batches[2]) == 1
        
        # Проверяем содержимое
        assert batches[0][0].email == "user0@example.com"
        assert batches[1][0].email == "user3@example.com"
        assert batches[2][0].email == "user6@example.com"
    
    def test_batch_stream_exact_division(self, loader):
        """Тест когда количество точно делится на размер батча."""
        def data_source():
            for i in range(6):
                yield {"email": f"user{i}@example.com", "name": f"User {i}"}
        
        batches = list(loader.batch_stream(data_source(), batch_size=2))
        
        assert len(batches) == 3
        assert all(len(batch) == 2 for batch in batches)
    
    def test_batch_stream_single_item(self, loader):
        """Тест с одним элементом в источнике."""
        def data_source():
            yield {"email": "single@example.com", "name": "Single User"}
        
        batches = list(loader.batch_stream(data_source(), batch_size=5))
        
        assert len(batches) == 1
        assert len(batches[0]) == 1
        assert batches[0][0].email == "single@example.com"
    
    def test_batch_stream_empty_after_filtering(self, loader):
        """Тест когда после фильтрации не остается валидных записей."""
        def data_source():
            yield {"name": "No Email 1"}
            yield {"name": "No Email 2"}
            yield "Invalid Data"
        
        batches = list(loader.batch_stream(data_source(), batch_size=2))
        assert len(batches) == 0
    
    def test_batch_stream_large_batch_size(self, loader):
        """Тест с размером батча больше количества данных."""
        def data_source():
            for i in range(3):
                yield {"email": f"user{i}@example.com", "name": f"User {i}"}
        
        batches = list(loader.batch_stream(data_source(), batch_size=10))
        
        assert len(batches) == 1
        assert len(batches[0]) == 3
    
    def test_batch_stream_with_invalid_mixed(self, loader):
        """Тест пакетной обработки со смешанными валидными и невалидными данными."""
        def data_source():
            yield {"email": "valid1@example.com", "name": "Valid 1"}
            yield {"name": "Invalid - no email"}
            yield {"email": "valid2@example.com", "name": "Valid 2"}
            yield {"email": "", "name": "Invalid - empty email"}
            yield {"email": "valid3@example.com", "name": "Valid 3"}
        
        batches = list(loader.batch_stream(data_source(), batch_size=2))
        
        assert len(batches) == 2  # [2, 1] валидных записей
        assert len(batches[0]) == 2
        assert len(batches[1]) == 1
        
        all_recipients = [r for batch in batches for r in batch]
        assert len(all_recipients) == 3
        assert all_recipients[0].email == "valid1@example.com"
        assert all_recipients[1].email == "valid2@example.com"
        assert all_recipients[2].email == "valid3@example.com"
    
    def test_stream_generator_exhaustion(self, loader):
        """Тест что генератор может быть использован только один раз."""
        def data_source():
            yield {"email": "test@example.com", "name": "Test"}
        
        generator = data_source()
        
        # Первое использование
        recipients1 = list(loader.stream(generator))
        assert len(recipients1) == 1
        
        # Второе использование того же генератора
        recipients2 = list(loader.stream(generator))
        assert len(recipients2) == 0  # Генератор исчерпан
    
    def test_stream_memory_efficiency_concept(self, loader):
        """Тест концепции эффективности памяти (не загружает все сразу)."""
        call_count = 0
        
        def data_source():
            nonlocal call_count
            for i in range(1000):
                call_count += 1
                yield {"email": f"user{i}@example.com", "name": f"User {i}"}
        
        # Берем только первые 5 элементов
        recipients = []
        for i, recipient in enumerate(loader.stream(data_source())):
            recipients.append(recipient)
            if i >= 4:  # Берем только 5 элементов
                break
        
        assert len(recipients) == 5
        # call_count должен быть примерно 5, а не 1000
        # (может быть немного больше из-за внутренней буферизации)
        assert call_count <= 10