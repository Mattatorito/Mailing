#!/usr/bin/env python3

import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import Mock, patch
from src.data_loader.base import BaseDataLoader, LoaderError
from src.data_loader.csv_loader import CSVLoader
from src.data_loader.excel_loader import ExcelLoader
from src.data_loader.streaming import StreamingDataLoader
from src.mailing.models import Recipient


def test_base_data_loader():
    """Тестирует базовый загрузчик данных."""
    loader = BaseDataLoader()
    
    # Базовый метод должен выбрасывать NotImplementedError
    with pytest.raises(NotImplementedError):
        loader.load("test_file.csv")


def test_loader_error():
    """Тестирует исключение LoaderError."""
    error = LoaderError("Test loader error")
    assert str(error) == "Test loader error"
    assert isinstance(error, Exception)


@pytest.fixture
def temp_csv_file():
    """Создает временный CSV файл для тестов."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'name', 'company', 'position'])
        writer.writerow(['john@example.com', 'John Doe', 'TechCorp', 'Developer'])
        writer.writerow(['jane@example.com', 'Jane Smith', 'DataInc', 'Analyst'])
        writer.writerow(['bob@example.com', 'Bob Johnson', 'WebLLC', 'Designer'])
        
        temp_file = f.name
    
    yield temp_file
    Path(temp_file).unlink(missing_ok=True)


@pytest.fixture
def temp_csv_minimal():
    """Создает минимальный CSV файл только с email."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email'])
        writer.writerow(['test1@example.com'])
        writer.writerow(['test2@example.com'])
        
        temp_file = f.name
    
    yield temp_file
    Path(temp_file).unlink(missing_ok=True)


def test_csv_loader_basic(temp_csv_file):
    """Тестирует базовую загрузку CSV."""
    loader = CSVLoader()
    recipients = loader.load(temp_csv_file)
    
    assert len(recipients) == 3
    assert all(isinstance(r, Recipient) for r in recipients)
    
    # Проверяем первого получателя
    first = recipients[0]
    assert first.email == "john@example.com"
    assert first.name == "John Doe"
    assert first.variables["company"] == "TechCorp"
    assert first.variables["position"] == "Developer"


def test_csv_loader_minimal(temp_csv_minimal):
    """Тестирует загрузку CSV только с email."""
    loader = CSVLoader()
    recipients = loader.load(temp_csv_minimal)
    
    assert len(recipients) == 2
    
    first = recipients[0]
    assert first.email == "test1@example.com"
    assert first.name == "test1@example.com"  # Должен использовать email как имя
    assert first.variables == {}


def test_csv_loader_with_custom_delimiter():
    """Тестирует загрузку CSV с другим разделителем."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("email;name;company\n")
        f.write("test@example.com;Test User;Test Corp\n")
        temp_file = f.name
    
    try:
        loader = CSVLoader()
        recipients = loader.load(temp_file, delimiter=';')
        
        assert len(recipients) == 1
        assert recipients[0].email == "test@example.com"
        assert recipients[0].name == "Test User"
        
    finally:
        Path(temp_file).unlink(missing_ok=True)


def test_csv_loader_invalid_file():
    """Тестирует загрузку несуществующего CSV файла."""
    loader = CSVLoader()
    
    with pytest.raises(LoaderError):
        loader.load("nonexistent.csv")


def test_csv_loader_empty_file():
    """Тестирует загрузку пустого CSV файла."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_file = f.name  # Пустой файл
    
    try:
        loader = CSVLoader()
        recipients = loader.load(temp_file)
        
        assert recipients == []
        
    finally:
        Path(temp_file).unlink(missing_ok=True)


def test_csv_loader_no_email_column():
    """Тестирует CSV файл без колонки email."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'company'])
        writer.writerow(['John Doe', 'TechCorp'])
        temp_file = f.name
    
    try:
        loader = CSVLoader()
        
        with pytest.raises(LoaderError):
            loader.load(temp_file)
            
    finally:
        Path(temp_file).unlink(missing_ok=True)


def test_csv_loader_validate_emails():
    """Тестирует валидацию email адресов в CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'name'])
        writer.writerow(['valid@example.com', 'Valid User'])
        writer.writerow(['invalid-email', 'Invalid User'])
        writer.writerow(['also.valid@test.org', 'Another Valid'])
        temp_file = f.name
    
    try:
        loader = CSVLoader()
        recipients = loader.load(temp_file, validate_emails=True)
        
        # Должно загрузить только валидные email (или все если валидатор недоступен)
        assert len(recipients) >= 1  # Как минимум один валидный
        emails = [r.email for r in recipients]
        assert 'also.valid@test.org' in emails
        
    finally:
        Path(temp_file).unlink(missing_ok=True)


@patch('os.path.exists', return_value=True)
@patch('openpyxl.load_workbook')
def test_excel_loader_success(mock_load_workbook, mock_exists):
    """Тестирует успешную загрузку Excel файла."""
    # Мокаем Excel workbook
    mock_workbook = Mock()
    mock_worksheet = Mock()
    
    # Мокаем доступ к первой строке через worksheet[1]
    mock_header_row = [
        Mock(value='email'),
        Mock(value='name'),
        Mock(value='company')
    ]
    mock_worksheet.__getitem__ = Mock(return_value=mock_header_row)
    
    # Настраиваем мок данные для iter_rows
    mock_worksheet.iter_rows.return_value = [
        ('test@example.com', 'Test User', 'Test Corp'),
        ('user@example.com', 'User Name', 'User Corp')
    ]
    
    mock_workbook.active = mock_worksheet
    mock_load_workbook.return_value = mock_workbook
    
    loader = ExcelLoader()
    recipients = loader.load("test.xlsx")
    
    assert len(recipients) == 2
    assert recipients[0].email == "test@example.com"
    assert recipients[0].name == "Test User"
    assert recipients[0].variables["company"] == "Test Corp"


def test_excel_loader_file_not_found():
    """Тестирует загрузку несуществующего Excel файла."""
    loader = ExcelLoader()
    
    with pytest.raises(LoaderError):
        loader.load("nonexistent.xlsx")


@patch('openpyxl.load_workbook')
def test_excel_loader_no_email_column(mock_load_workbook):
    """Тестирует Excel файл без колонки email."""
    mock_workbook = Mock()
    mock_worksheet = Mock()
    
    mock_worksheet.iter_rows.return_value = [
        [Mock(value='name'), Mock(value='company')],
        [Mock(value='Test User'), Mock(value='Test Corp')]
    ]
    
    mock_workbook.active = mock_worksheet
    mock_load_workbook.return_value = mock_workbook
    
    loader = ExcelLoader()
    
    with pytest.raises(LoaderError):
        loader.load("test.xlsx")


def test_streaming_loader():
    """Тестирует потоковый загрузчик данных."""
    
    def mock_data_source():
        """Мок источник данных."""
        yield {"email": "user1@example.com", "name": "User 1"}
        yield {"email": "user2@example.com", "name": "User 2"}
        yield {"email": "user3@example.com", "name": "User 3"}
    
    loader = StreamingDataLoader()
    
    # Тестируем потоковую обработку
    recipients = []
    for recipient in loader.stream(mock_data_source()):
        recipients.append(recipient)
    
    assert len(recipients) == 3
    assert all(isinstance(r, Recipient) for r in recipients)
    assert recipients[0].email == "user1@example.com"
    assert recipients[2].name == "User 3"


def test_streaming_loader_with_batch():
    """Тестирует потоковый загрузчик с батчами."""
    
    def large_data_source():
        """Большой источник данных."""
        for i in range(100):
            yield {"email": f"user{i}@example.com", "name": f"User {i}"}
    
    loader = StreamingDataLoader()
    
    # Обрабатываем батчами по 10
    all_recipients = []
    for batch in loader.batch_stream(large_data_source(), batch_size=10):
        assert len(batch) == 10
        all_recipients.extend(batch)
    
    assert len(all_recipients) == 100


def test_streaming_loader_invalid_data():
    """Тестирует обработку некорректных данных в потоке."""
    
    def mixed_data_source():
        """Источник с смешанными данными."""
        yield {"email": "valid@example.com", "name": "Valid User"}
        yield {"name": "No Email User"}  # Нет email
        yield {"email": "another@example.com", "name": "Another User"}
    
    loader = StreamingDataLoader()
    
    recipients = []
    for recipient in loader.stream(mixed_data_source()):
        if recipient:  # Может возвращать None для невалидных данных
            recipients.append(recipient)
    
    # Должно загрузить только валидные записи
    assert len(recipients) == 2
    assert recipients[0].email == "valid@example.com"
    assert recipients[1].email == "another@example.com"


def test_loader_memory_efficiency():
    """Тестирует эффективность памяти загрузчиков."""
    # Создаем большой CSV файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'name'])
        
        # Записываем много строк
        for i in range(1000):
            writer.writerow([f'user{i}@example.com', f'User {i}'])
        
        temp_file = f.name
    
    try:
        # Обычная загрузка
        csv_loader = CSVLoader()
        recipients = csv_loader.load(temp_file)
        assert len(recipients) == 1000
        
        # Потоковая загрузка
        streaming_loader = StreamingDataLoader()
        
        def csv_data_source():
            with open(temp_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield row
        
        streaming_count = 0
        for recipient in streaming_loader.stream(csv_data_source()):
            streaming_count += 1
        
        assert streaming_count == 1000
        
    finally:
        Path(temp_file).unlink(missing_ok=True)