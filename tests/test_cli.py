#!/usr/bin/env python3

import pytest
import json
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from src.mailing.cli import load_recipients, load_json_recipients, send_all
from src.mailing.models import Recipient


@pytest.fixture
def temp_csv_file():
    """Создает временный CSV файл для тестов."""
    content = """email,name,company
test1@example.com,John Doe,Company A
test2@example.com,Jane Smith,Company B
test3@example.com,Bob Johnson,Company C
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        f.flush()  # Принудительно записываем данные
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_json_file():
    """Создает временный JSON файл для тестов."""
    data = [
        {"email": "test1@example.com", "name": "John Doe", "company": "Company A"},
        {"email": "test2@example.com", "name": "Jane Smith", "company": "Company B"},
        {"email": "test3@example.com", "name": "Bob Johnson", "company": "Company C"}
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()  # Принудительно записываем данные
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_xlsx_file():
    """Создает временный XLSX файл для тестов."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        # Создаем простой Excel файл
        yield f.name
    Path(f.name).unlink(missing_ok=True)


def test_load_json_recipients(temp_json_file):
    """Тестирует загрузку получателей из JSON файла."""
    recipients = load_json_recipients(temp_json_file)
    
    assert len(recipients) == 3
    assert all(isinstance(r, Recipient) for r in recipients)
    
    # Проверяем первого получателя
    first = recipients[0]
    assert first.email == "test1@example.com"
    assert first.name == "John Doe"
    assert first.variables["company"] == "Company A"


def test_load_json_recipients_invalid_format():
    """Тестирует загрузку из некорректного JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([{"invalid": "data"}], f)
        temp_file = f.name
    
    try:
        recipients = load_json_recipients(temp_file)
        assert len(recipients) == 0  # Пустой список для некорректных данных
    finally:
        Path(temp_file).unlink(missing_ok=True)


@patch('mailing.cli.CSVLoader')
def test_load_recipients_csv(mock_csv_loader, temp_csv_file):
    """Тестирует загрузку получателей из CSV файла."""
    mock_loader = Mock()
    mock_loader.load.return_value = [
        Recipient(email="test@example.com", name="Test User", variables={})
    ]
    mock_csv_loader.return_value = mock_loader
    
    recipients = load_recipients(temp_csv_file)
    
    mock_csv_loader.assert_called_once()
    mock_loader.load.assert_called_once_with(temp_csv_file)
    assert len(recipients) == 1


@patch('mailing.cli.ExcelLoader')
def test_load_recipients_excel(mock_excel_loader, temp_xlsx_file):
    """Тестирует загрузку получателей из Excel файла."""
    mock_loader = Mock()
    mock_loader.load.return_value = [
        Recipient(email="test@example.com", name="Test User", variables={})
    ]
    mock_excel_loader.return_value = mock_loader
    
    recipients = load_recipients(temp_xlsx_file)
    
    mock_excel_loader.assert_called_once()
    mock_loader.load.assert_called_once_with(temp_xlsx_file)
    assert len(recipients) == 1


def test_load_recipients_json_direct(temp_json_file):
    """Тестирует прямую загрузку JSON файла."""
    recipients = load_recipients(temp_json_file)
    
    assert len(recipients) == 3
    assert recipients[0].email == "test1@example.com"


def test_load_recipients_nonexistent_file():
    """Тестирует обработку несуществующего файла."""
    with pytest.raises(FileNotFoundError):
        load_recipients("nonexistent_file.csv")


def test_load_recipients_unsupported_format():
    """Тестирует обработку неподдерживаемого формата файла."""
    with tempfile.NamedTemporaryFile(suffix='.txt') as temp_file:
        with pytest.raises(ValueError):
            load_recipients(temp_file.name)


@pytest.mark.asyncio
@patch('mailing.cli.run_campaign')
async def test_send_all_success(mock_run_campaign, temp_json_file):
    """Тестирует успешную отправку кампании."""
    # Мокаем события кампании
    mock_events = [
        {'type': 'progress', 'sent': 1, 'total': 3},
        {'type': 'progress', 'sent': 2, 'total': 3},
        {'type': 'finished', 'stats': {'sent': 3, 'delivered': 3, 'failed': 0}}
    ]
    
    async def async_generator():
        for event in mock_events:
            yield event
    
    mock_run_campaign.return_value = async_generator()
    
    # Запускаем тест
    await send_all(
        recipients_file=temp_json_file,
        template_name="test_template.html",
        subject="Test Subject",
        dry_run=True
    )
    
    # Проверяем что run_campaign была вызвана
    mock_run_campaign.assert_called_once()
    args, kwargs = mock_run_campaign.call_args
    
    assert len(kwargs['recipients']) == 3
    assert kwargs['template_name'] == "test_template.html"
    assert kwargs['subject'] == "Test Subject"
    assert kwargs['dry_run'] == True


@pytest.mark.asyncio
@patch('src.mailing.cli.load_recipients')
async def test_send_all_load_error(mock_load_recipients):
    """Тестирует обработку ошибки загрузки получателей."""
    mock_load_recipients.side_effect = Exception("Load error")
    
    # Функция должна вернуть False при ошибке загрузки
    result = await send_all(
        recipients_file="test.json",
        template_name="test_template.html",
        subject="Test Subject"
    )
    
    assert result is False, "Function should return False on load error"
    mock_load_recipients.assert_called_once_with("test.json")


@pytest.mark.asyncio
@patch('mailing.cli.run_campaign')
async def test_send_all_campaign_error(mock_run_campaign, temp_json_file):
    """Тестирует обработку ошибки в кампании."""
    mock_events = [
        {'type': 'error', 'message': 'Campaign failed'}
    ]
    
    async def async_generator():
        for event in mock_events:
            yield event
    
    mock_run_campaign.return_value = async_generator()
    
    # Функция должна вернуть False при ошибке кампании
    result = await send_all(
        recipients_file=temp_json_file,
        template_name="test_template.html",
        subject="Test Subject"
    )
    
    assert result is False, "Function should return False on campaign error"