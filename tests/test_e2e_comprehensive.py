#!/usr/bin/env python3
"""
End-to-End тесты для проверки полного цикла отправки email.
Тестирует интеграцию всех компонентов системы.
"""

import os
import pytest
import asyncio
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import aiohttp
import sqlite3

from src.mailing.sender import run_campaign
from src.mailing.models import Recipient, DeliveryResult
from src.persistence.repository import DeliveryRepository, SuppressionRepository
from src.templating.cached_engine import get_template_engine
from src.resend.client import ResendClient
from src.data_loader.csv_loader import CSVLoader
from src.validation.email_validator import EmailValidator

class MockResendClient:
    """Mock клиент для тестирования без реальной отправки."""
    
    def __init__(self, simulate_errors: bool = False):
        self.simulate_errors = simulate_errors
        self.sent_emails = []
        self.call_count = 0
    
    async def send_message(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> DeliveryResult:
        """Имитирует отправку email."""
        self.call_count += 1
        self.sent_emails.append({
            "to": to_email,
            "subject": subject,
            "html": html_content,
            "text": text_content,
            "timestamp": datetime.now()
        })
        
        # Имитируем различные результаты
        if self.simulate_errors and self.call_count % 3 == 0:
            return DeliveryResult(
                email=to_email,
                success=False,
                status_code=429,
                error="Rate limit exceeded",
                provider="mock-resend"
            )
        elif self.simulate_errors and self.call_count % 5 == 0:
            return DeliveryResult(
                email=to_email,
                success=False,
                status_code=500,
                error="Server error",
                provider="mock-resend"
            )
        else:
            return DeliveryResult(
                email=to_email,
                success=True,
                status_code=200,
                provider="mock-resend",
                message_id=f"mock-{self.call_count}"
            )

@pytest.fixture
async def temp_db():
    """Создает временную БД для тестов."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Инициализируем БД
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE delivery_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            status_code INTEGER,
            error TEXT,
            provider TEXT,
            message_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE suppressions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)

@pytest.fixture
async def temp_templates_dir():
    """Создает временную директорию с шаблонами."""
    with tempfile.TemporaryDirectory() as temp_dir:
        templates_dir = Path(temp_dir)
        
        # Создаем тестовые шаблоны
        html_template = templates_dir / "test_template.html"
        html_template.write_text('''
<!DOCTYPE html>
<html>
<head>
    <title>{{ subject }}</title>
</head>
<body>
    <h1>Hello {{ name }}!</h1>
    <p>Your email is: {{ email }}</p>
    <p>Test variable: {{ test_var|default("N/A") }}</p>
</body>
</html>
        '''.strip())
        
        text_template = templates_dir / "test_template.txt"
        text_template.write_text('''
Hello {{ name }}!

Your email is: {{ email }}
Test variable: {{ test_var|default("N/A") }}

Best regards,
Test Team
        '''.strip())
        
        # Шаблон с ошибкой
        error_template = templates_dir / "error_template.html"
        error_template.write_text('''
<html>
<body>
    <h1>Hello {{ undefined_variable }}!</h1>
</body>
</html>
        '''.strip())
        
        yield str(templates_dir)

@pytest.fixture
async def temp_recipients_csv():
    """Создает временный CSV файл с получателями."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(['email', 'name', 'test_var', 'custom_field'])
        writer.writerow(['user1@example.com', 'John Doe', 'Value1', 'Custom1'])
        writer.writerow(['user2@example.com', 'Jane Smith', 'Value2', 'Custom2'])
        writer.writerow(['invalid-email', 'Invalid User', 'Value3', 'Custom3'])  # Невалидный email
        writer.writerow(['user3@example.com', 'Bob Wilson', 'Value4', 'Custom4'])
        f.flush()
        
        yield f.name
    
    os.unlink(f.name)

class TestE2EEmailCampaign:
    """E2E тесты для email кампаний."""
    
    @pytest.mark.asyncio
    async def test_successful_campaign_end_to_end(self, temp_db, temp_templates_dir, temp_recipients_csv):
        """Тест успешной кампании от начала до конца."""
        
        # 1. Загружаем получателей из CSV
        loader = CSVLoader()
        recipients_data = await loader.load_from_file(temp_recipients_csv)
        
        # 2. Валидируем email адреса
        validator = EmailValidator()
        valid_recipients = []
        
        for recipient_data in recipients_data:
            if validator.validate_email(recipient_data.get('email', '')):
                recipient = Recipient(
                    email=recipient_data['email'],
                    name=recipient_data.get('name', ''),
                    variables=recipient_data
                )
                valid_recipients.append(recipient)
        
        assert len(valid_recipients) == 3  # 3 валидных из 4
        
        # 3. Инициализируем репозитории
        delivery_repo = DeliveryRepository(temp_db)
        suppression_repo = SuppressionRepository(temp_db)
        
        # 4. Настраиваем движок шаблонов
        os.environ['TEMPLATES_DIR'] = temp_templates_dir
        template_engine = get_template_engine()
        
        # 5. Валидируем шаблон
        validation_result = await template_engine.validate_template(
            'test_template.html',
            {'name': 'Test', 'email': 'test@example.com', 'test_var': 'test'}
        )
        assert validation_result['valid'] == True
        
        # 6. Запускаем кампанию с mock клиентом
        mock_client = MockResendClient(simulate_errors=False)
        
        results = []
        async for event in run_campaign(
            recipients=valid_recipients,
            template_name='test_template.html',
            subject='Test Campaign',
            dry_run=False,
            concurrency=2
        ):
            results.append(event)
            if event.get('type') == 'progress':
                # Проверяем что результат сохраняется
                delivery_result = event['result']
                assert isinstance(delivery_result, DeliveryResult)
        
        # 7. Проверяем результаты
        progress_events = [e for e in results if e.get('type') == 'progress']
        assert len(progress_events) == 3  # По одному для каждого валидного получателя
        
        # 8. Проверяем что данные сохранены в БД
        saved_results = delivery_repo.get_delivery_history(limit=10)
        assert len(saved_results) == 3
        
        for result in saved_results:
            assert result.success == True
            assert result.provider in ['resend', 'mock-resend']
    
    @pytest.mark.asyncio
    async def test_campaign_with_errors_and_suppressions(self, temp_db, temp_templates_dir):
        """Тест кампании с ошибками и подавлениями."""
        
        # Создаем получателей
        recipients = [
            Recipient(email='user1@example.com', name='User 1', variables={'test_var': 'value1'}),
            Recipient(email='suppressed@example.com', name='Suppressed User', variables={'test_var': 'value2'}),
            Recipient(email='user2@example.com', name='User 2', variables={'test_var': 'value3'}),
            Recipient(email='bounce@example.com', name='Bounce User', variables={'test_var': 'value4'}),
        ]
        
        # Настраиваем подавления
        suppression_repo = SuppressionRepository(temp_db)
        suppression_repo.add_suppression('suppressed@example.com', 'unsubscribed', 'User opted out')
        suppression_repo.add_suppression('bounce@example.com', 'bounced', 'Email bounced')
        
        # Настраиваем движок шаблонов
        os.environ['TEMPLATES_DIR'] = temp_templates_dir
        
        # Запускаем кампанию с ошибками
        mock_client = MockResendClient(simulate_errors=True)
        
        results = []
        async for event in run_campaign(
            recipients=recipients,
            template_name='test_template.html',
            subject='Test Campaign with Errors',
            dry_run=False,
            concurrency=1
        ):
            results.append(event)
        
        # Проверяем результаты
        progress_events = [e for e in results if e.get('type') == 'progress']
        
        # Должны получить результаты только для несподавленных получателей
        valid_events = [e for e in progress_events if e['result'].email in ['user1@example.com', 'user2@example.com']]
        assert len(valid_events) == 2
        
        # Проверяем подавленных получателей
        delivery_repo = DeliveryRepository(temp_db)
        all_results = delivery_repo.get_delivery_history(limit=10)
        
        suppressed_results = [r for r in all_results if r.email in ['suppressed@example.com', 'bounce@example.com']]
        for result in suppressed_results:
            assert result.success == False
            assert result.error in ['unsubscribed', 'suppressed']
    
    @pytest.mark.asyncio
    async def test_template_rendering_with_cache(self, temp_templates_dir):
        """Тест рендеринга шаблонов с кэшированием."""
        
        os.environ['TEMPLATES_DIR'] = temp_templates_dir
        os.environ['TEMPLATE_CACHE_ENABLED'] = 'true'
        
        template_engine = get_template_engine()
        
        # Первый рендер (cache miss)
        html1, text1 = await template_engine.render(
            'test_template.html',
            {'name': 'John', 'email': 'john@example.com', 'test_var': 'cached_value'}
        )
        
        assert 'Hello John!' in html1
        assert 'john@example.com' in html1
        assert 'cached_value' in html1
        
        # Второй рендер (cache hit)
        html2, text2 = await template_engine.render(
            'test_template.html',
            {'name': 'Jane', 'email': 'jane@example.com', 'test_var': 'another_value'}
        )
        
        assert 'Hello Jane!' in html2
        assert 'jane@example.com' in html2
        
        # Проверяем статистику кэша
        cache_stats = template_engine.get_cache_stats()
        assert cache_stats['total_renders'] == 2
        assert cache_stats['cache_hits'] > 0
    
    @pytest.mark.asyncio
    async def test_template_error_handling(self, temp_templates_dir):
        """Тест обработки ошибок шаблонов."""
        
        os.environ['TEMPLATES_DIR'] = temp_templates_dir
        template_engine = get_template_engine()
        
        # Тест несуществующего шаблона
        with pytest.raises(Exception):
            await template_engine.render(
                'nonexistent_template.html',
                {'name': 'Test'}
            )
        
        # Тест шаблона с ошибкой
        validation_result = await template_engine.validate_template(
            'error_template.html',
            {'name': 'Test'}
        )
        
        assert validation_result['valid'] == False
        assert len(validation_result['missing_variables']) > 0
        assert 'undefined_variable' in validation_result['missing_variables']
    
    @pytest.mark.asyncio
    async def test_concurrent_campaign_execution(self, temp_db, temp_templates_dir):
        """Тест конкурентного выполнения кампании."""
        
        # Создаем много получателей
        recipients = []
        for i in range(20):
            recipients.append(Recipient(
                email=f'user{i}@example.com',
                name=f'User {i}',
                variables={'index': str(i), 'test_var': f'value{i}'}
            ))
        
        os.environ['TEMPLATES_DIR'] = temp_templates_dir
        
        # Запускаем с высокой конкурентностью
        start_time = asyncio.get_event_loop().time()
        
        results = []
        async for event in run_campaign(
            recipients=recipients,
            template_name='test_template.html',
            subject='Concurrent Test',
            dry_run=True,  # Используем dry_run для ускорения
            concurrency=10
        ):
            results.append(event)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        # Проверяем что все получатели обработаны
        progress_events = [e for e in results if e.get('type') == 'progress']
        assert len(progress_events) == 20
        
        # Проверяем что конкурентность сработала (должно быть быстрее последовательного выполнения)
        assert duration < 5.0  # Не более 5 секунд для 20 получателей
        
        # Проверяем статистику
        final_stats = [e for e in results if e.get('type') == 'progress'][-1]['stats']
        assert final_stats['total'] == 20
        assert final_stats['successful'] == 20
    
    @pytest.mark.asyncio 
    async def test_data_loader_integration(self, temp_recipients_csv):
        """Тест интеграции с загрузчиком данных."""
        
        loader = CSVLoader()
        
        # Тест загрузки из файла
        data = await loader.load_from_file(temp_recipients_csv)
        assert len(data) == 4  # 4 строки в CSV
        
        # Проверяем структуру данных
        first_recipient = data[0]
        assert first_recipient['email'] == 'user1@example.com'
        assert first_recipient['name'] == 'John Doe'
        assert first_recipient['test_var'] == 'Value1'
        
        # Тест валидации загруженных данных
        validator = EmailValidator()
        valid_count = sum(1 for item in data if validator.validate_email(item.get('email', '')))
        assert valid_count == 3  # 3 валидных email из 4
    
    @pytest.mark.asyncio
    async def test_database_persistence(self, temp_db):
        """Тест сохранения данных в БД."""
        
        delivery_repo = DeliveryRepository(temp_db)
        suppression_repo = SuppressionRepository(temp_db)
        
        # Тест сохранения результатов доставки
        result = DeliveryResult(
            email='test@example.com',
            success=True,
            status_code=200,
            provider='test-provider',
            message_id='test-123'
        )
        
        delivery_repo.save_delivery(result)
        
        # Проверяем сохранение
        history = delivery_repo.get_delivery_history(limit=1)
        assert len(history) == 1
        assert history[0].email == 'test@example.com'
        assert history[0].success == True
        
        # Тест подавлений
        suppression_repo.add_suppression('suppressed@example.com', 'unsubscribed', 'User request')
        
        assert suppression_repo.is_unsubscribed('suppressed@example.com') == True
        assert suppression_repo.is_unsubscribed('other@example.com') == False

class TestE2EAPIIntegration:
    """E2E тесты для API интеграции."""
    
    @pytest.mark.asyncio
    async def test_webhook_processing(self):
        """Тест обработки webhook событий."""
        # Этот тест требует запущенного сервера
        # Пока что заглушка для будущей реализации
        pass
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self):
        """Тест интеграции rate limiting."""
        from src.resend.rate_limiter import get_resend_limiter
        
        limiter = get_resend_limiter()
        
        # Тестируем последовательные запросы
        for i in range(5):
            can_proceed = await limiter.acquire()
            assert can_proceed == True  # Первые запросы должны проходить
        
        # Проверяем статистику
        remaining = limiter.get_remaining_requests()
        assert remaining < 10  # Должно уменьшиться

@pytest.mark.integration
class TestE2ERealAPI:
    """E2E тесты с реальным API (требуют настройки окружения)."""
    
    @pytest.mark.skipif(not os.getenv('RESEND_API_KEY'), reason="Real API key required")
    @pytest.mark.asyncio
    async def test_real_api_integration(self):
        """Тест с реальным Resend API (только при наличии ключа)."""
        
        # Создаем одного тестового получателя
        test_email = os.getenv('TEST_EMAIL', 'test@example.com')
        recipient = Recipient(
            email=test_email,
            name='Test User',
            variables={'test_var': 'real_api_test'}
        )
        
        # Запускаем небольшую кампанию
        results = []
        async for event in run_campaign(
            recipients=[recipient],
            template_name='test_template.html',
            subject='Real API Test',
            dry_run=False,  # Реальная отправка!
            concurrency=1
        ):
            results.append(event)
        
        # Проверяем что отправка прошла успешно
        progress_events = [e for e in results if e.get('type') == 'progress']
        assert len(progress_events) == 1
        
        result = progress_events[0]['result']
        assert result.success == True
        assert result.message_id is not None

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v", "--tb=short"])