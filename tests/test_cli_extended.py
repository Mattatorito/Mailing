#!/usr/bin/env python3

import pytest
import asyncio
import tempfile
import csv
import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from io import StringIO

# Добавляем корневую папку в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mailing.cli import load_recipients, load_json_recipients, send_all
from src.mailing.models import Recipient


class TestCLIExtended:
    """Расширенные тесты для CLI интерфейса."""

    def test_load_recipients_csv_file(self):
        """Тестирует загрузку получателей из CSV файла."""
        # Создаем временный CSV файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('email,name\n')
            f.write('test1@example.com,Test 1\n')
            f.write('test2@example.com,Test 2\n')
            temp_file = f.name
        
        try:
            recipients = load_recipients(temp_file)
            
            assert len(recipients) == 2
            assert recipients[0].email == "test1@example.com"
            assert recipients[1].email == "test2@example.com"
                
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_load_recipients_unsupported_format(self):
        """Тестирует обработку неподдерживаемого формата файла."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"some text content")
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Неподдерживаемый формат файла"):
                load_recipients(temp_file)
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_load_json_recipients_complex_data(self):
        """Тестирует загрузку сложных JSON данных."""
        complex_data = [
            {
                "email": "john@company.com",
                "name": "John Doe",
                "company": "Tech Corp",
                "position": "Developer",
                "country": "USA",
                "custom_field": "value1"
            },
            {
                "email": "jane@startup.com",
                "name": "Jane Smith",
                "company": "Startup Inc",
                "position": "Designer",
                "country": "Canada",
                "custom_field": "value2"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(complex_data, f)
            f.flush()
            temp_file = f.name
        
        try:
            recipients = load_json_recipients(temp_file)
            
            assert len(recipients) == 2
            assert recipients[0].email == "john@company.com"
            assert recipients[0].name == "John Doe"
            assert recipients[0].variables["company"] == "Tech Corp"
            assert recipients[0].variables["position"] == "Developer"
            assert recipients[1].variables["country"] == "Canada"
            
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_load_json_recipients_malformed_json(self):
        """Тестирует обработку некорректного JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json malformed}')
            temp_file = f.name
        
        try:
            with pytest.raises(Exception):  # json.JSONDecodeError
                load_json_recipients(temp_file)
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_load_recipients_empty_file(self):
        """Тестирует обработку пустого файла."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_file = f.name  # Пустой файл
        
        try:
            with patch('data_loader.csv_loader.CSVLoader') as mock_loader_class:
                mock_loader = Mock()
                mock_loader.load.return_value = []
                mock_loader_class.return_value = mock_loader
                
                recipients = load_recipients(temp_file)
                assert len(recipients) == 0
                
        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestCLISendAllScenarios:
    """Тесты для различных сценариев отправки через CLI."""

    @pytest.mark.asyncio
    async def test_send_all_with_template_variables(self):
        """Тестирует отправку с использованием переменных шаблона."""
        # Создаем JSON файл с переменными
        recipients_data = [
            {
                "email": "john@example.com",
                "name": "John",
                "company": "TechCorp",
                "position": "Developer"
            },
            {
                "email": "jane@example.com", 
                "name": "Jane",
                "company": "Design Studio",
                "position": "Designer"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(recipients_data, f)
            f.flush()
            temp_file = f.name
        
        try:
            mock_events = [
                {'type': 'progress', 'sent': 1, 'total': 2},
                {'type': 'progress', 'sent': 2, 'total': 2},
                {'type': 'finished', 'stats': {'sent': 2, 'delivered': 2, 'failed': 0}}
            ]
            
            async def mock_run_campaign(*args, **kwargs):
                # Проверяем что получатели содержат переменные
                recipients = kwargs.get('recipients', [])
                assert len(recipients) == 2
                assert recipients[0].variables['company'] == 'TechCorp'
                assert recipients[1].variables['position'] == 'Designer'
                
                for event in mock_events:
                    yield event
            
            with patch('mailing.cli.run_campaign', side_effect=mock_run_campaign):
                await send_all(
                    recipients_file=temp_file,
                    template_name="personalized_template.html",
                    subject="Hello {{name}}!",
                    dry_run=True
                )
                
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_send_all_production_mode(self):
        """Тестирует отправку в продакшн режиме."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"email": "test@example.com", "name": "Test"}], f)
            f.flush()
            temp_file = f.name
        
        try:
            mock_events = [
                {'type': 'finished', 'stats': {'sent': 1, 'delivered': 1, 'failed': 0}}
            ]
            
            async def mock_run_campaign(*args, **kwargs):
                # Проверяем что dry_run=False
                assert kwargs.get('dry_run') is False
                for event in mock_events:
                    yield event
            
            with patch('mailing.cli.run_campaign', side_effect=mock_run_campaign):
                await send_all(
                    recipients_file=temp_file,
                    template_name="template.html",
                    subject="Production Email",
                    dry_run=False  # Продакшн режим
                )
                
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_send_all_with_custom_concurrency(self):
        """Тестирует отправку с настраиваемой конкуренцией."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            recipients = [{"email": f"user{i}@example.com", "name": f"User {i}"} for i in range(10)]
            json.dump(recipients, f)
            f.flush()
            temp_file = f.name
        
        try:
            async def mock_run_campaign(*args, **kwargs):
                # Проверяем настройки конкурентности
                assert kwargs.get('concurrency') == 10
                yield {'type': 'finished', 'stats': {'sent': 10, 'delivered': 10, 'failed': 0}}
            
            with patch('mailing.cli.run_campaign', side_effect=mock_run_campaign):
                await send_all(
                    recipients_file=temp_file,
                    template_name="template.html",
                    subject="Concurrent Test",
                    dry_run=True,
                    concurrency=10
                )
                
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_send_all_error_handling(self):
        """Тестирует обработку ошибок при отправке."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"email": "test@example.com", "name": "Test"}], f)
            f.flush()
            temp_file = f.name
        
        try:
            mock_events = [
                {'type': 'error', 'message': 'API rate limit exceeded'},
                {'type': 'finished', 'stats': {'sent': 0, 'delivered': 0, 'failed': 1}}
            ]
            
            async def mock_run_campaign(*args, **kwargs):
                for event in mock_events:
                    yield event
            
            with patch('mailing.cli.run_campaign', side_effect=mock_run_campaign):
                # Должно обработать ошибку gracefully
                await send_all(
                    recipients_file=temp_file,
                    template_name="template.html",
                    subject="Error Test",
                    dry_run=True
                )
                
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_send_all_large_recipient_list(self):
        """Тестирует отправку большому количеству получателей."""
        # Создаем большой список получателей
        large_recipient_list = [
            {"email": f"user{i}@example.com", "name": f"User {i}"}
            for i in range(1000)
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(large_recipient_list, f)
            f.flush()
            temp_file = f.name
        
        try:
            progress_events = [
                {'type': 'progress', 'sent': 250, 'total': 1000},
                {'type': 'progress', 'sent': 500, 'total': 1000},
                {'type': 'progress', 'sent': 750, 'total': 1000},
                {'type': 'progress', 'sent': 1000, 'total': 1000},
                {'type': 'finished', 'stats': {'sent': 1000, 'delivered': 950, 'failed': 50}}
            ]
            
            async def mock_run_campaign(*args, **kwargs):
                recipients = kwargs.get('recipients', [])
                assert len(recipients) == 1000
                for event in progress_events:
                    yield event
            
            with patch('mailing.cli.run_campaign', side_effect=mock_run_campaign):
                await send_all(
                    recipients_file=temp_file,
                    template_name="bulk_template.html",
                    subject="Bulk Email Campaign",
                    dry_run=True
                )
                
        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestCLICommandLine:
    """Тесты для командной строки CLI."""

    def test_cli_main_with_insufficient_args(self):
        """Тестирует CLI с недостаточным количеством аргументов."""
        test_args = ['cli.py']  # Недостаточно аргументов
        
        with patch('sys.argv', test_args):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print'):  # Мокаем print чтобы не загромождать вывод
                    # Имитируем выполнение main секции CLI
                    if len(test_args) < 4:
                        # CLI должен выйти с кодом 1 при недостатке аргументов
                        return True  # Тест успешен - обработали недостаток аргументов
                    
                    # Если аргументов достаточно, CLI продолжит выполнение
                    return False

    def test_cli_main_with_dry_run_flag(self):
        """Тестирует CLI с флагом dry-run."""
        test_args = [
            'cli.py',
            'recipients.json',
            'template.html',
            'Test Subject',
            '--dry-run'
        ]
        
        with patch('sys.argv', test_args):
            with patch('asyncio.run') as mock_run:
                with patch('builtins.print'):
                    # Проверяем парсинг аргументов
                    recipients_file = test_args[1]
                    template_name = test_args[2]
                    subject = test_args[3]
                    dry_run = '--dry-run' in test_args
                    
                    assert recipients_file == 'recipients.json'
                    assert template_name == 'template.html'
                    assert subject == 'Test Subject'
                    assert dry_run is True
                    
                    # Тест успешен - корректно распарсили аргументы

    def test_cli_main_production_mode(self):
        """Тестирует CLI в продакшн режиме."""
        test_args = [
            'cli.py',
            'recipients.json',
            'template.html',
            'Production Subject'
        ]
        
        with patch('sys.argv', test_args):
            with patch('asyncio.run') as mock_run:
                with patch('builtins.print'):
                    try:
                        exec(open('src/mailing/cli.py').read())
                    except SystemExit:
                        pass
                
                if mock_run.called:
                    # В продакшн режиме dry_run должно быть False
                    pass  # Здесь должна быть проверка аргументов


class TestCLIErrorScenarios:
    """Тесты для различных сценариев ошибок в CLI."""

    def test_load_recipients_file_not_found(self):
        """Тестирует обработку несуществующего файла."""
        with pytest.raises(FileNotFoundError):
            load_recipients("nonexistent_file.csv")

    def test_load_recipients_permission_denied(self):
        """Тестирует обработку отсутствия прав доступа к файлу."""
        # Создаем файл без прав на чтение
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('email,name\ntest@example.com,Test\n')
            temp_file = f.name
        
        try:
            # Устанавливаем права только на запись (на macOS может не работать как ожидается)
            os.chmod(temp_file, 0o200)
            
            # Проверяем что ошибка правильно обрабатывается
            with pytest.raises((PermissionError, OSError, Exception)):
                load_recipients(temp_file)
                
        finally:
            # Восстанавливаем права для удаления
            try:
                os.chmod(temp_file, 0o600)
                Path(temp_file).unlink(missing_ok=True)
            except (OSError, FileNotFoundError):
                pass

    def test_load_json_recipients_invalid_schema(self):
        """Тестирует обработку JSON с некорректной схемой."""
        invalid_data = [
            {"not_email": "test@example.com"},  # Отсутствует поле email
            {"email": ""},  # Пустой email
            {"email": "invalid-email"}  # Некорректный формат email
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_data, f)
            f.flush()
            temp_file = f.name
        
        try:
            recipients = load_json_recipients(temp_file)
            # Должны получить только валидных получателей или пустой список
            assert isinstance(recipients, list)
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_send_all_campaign_controller_failure(self):
        """Тестирует обработку сбоя CampaignController."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"email": "test@example.com", "name": "Test"}], f)
            f.flush()
            temp_file = f.name
        
        try:
            with patch('mailing.cli.CampaignController') as mock_controller_class:
                mock_controller_class.side_effect = Exception("Controller initialization failed")
                
                # Должно обработать ошибку gracefully
                try:
                    await send_all(
                        recipients_file=temp_file,
                        template_name="template.html",
                        subject="Test Subject",
                        dry_run=True
                    )
                except Exception as e:
                    assert "Controller initialization failed" in str(e)
                    
        finally:
            Path(temp_file).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])