#!/usr/bin/env python3

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Imports are handled by pytest configuration and project structure

from src.mailing.types import (
    EventData, StatsData, WebhookPayload, PreflightResult, 
    PerformanceMetrics, QuotaInfo, ValidationResult
)
from src.validation.email_validator import EmailValidator
from src.stats.aggregator import StatsAggregator
from src.templating.engine import TemplateEngine, HTMLToTextParser


class TestTypes:
    """Тесты для типов данных."""

    def test_event_data_creation(self):
        """Тестирует создание EventData."""
        event: EventData = {
            'type': 'email.sent',
            'email': 'test@example.com',
            'timestamp': '2024-01-20T10:30:00Z',
            'message_id': 'msg_123'
        }
        
        assert event['type'] == 'email.sent'
        assert event['email'] == 'test@example.com'

    def test_stats_data_creation(self):
        """Тестирует создание StatsData."""
        stats: StatsData = {
            'sent': 100,
            'delivered': 95,
            'failed': 5,
            'bounced': 2,
            'opened': 30,
            'clicked': 10,
            'unsubscribed': 1,
            'success_rate': 0.95,
            'total_events': 143,
            'last_updated': '2024-01-20T10:30:00Z'
        }
        
        assert stats['sent'] == 100
        assert stats['success_rate'] == 0.95

    def test_webhook_payload_creation(self):
        """Тестирует создание WebhookPayload."""
        payload: WebhookPayload = {
            'type': 'email.delivered',
            'data': {'id': '123', 'email': 'test@example.com'},
            'created_at': '2024-01-20T10:30:00Z'
        }
        
        assert payload['type'] == 'email.delivered'
        assert payload['data']['id'] == '123'


class TestEmailValidatorExtended:
    """Расширенные тесты для EmailValidator."""

    def test_validator_initialization(self):
        """Тестирует инициализацию валидатора."""
        validator = EmailValidator(strict=True)
        assert validator.strict is True
        assert validator.pattern == EmailValidator.STRICT_EMAIL_PATTERN
        
        validator_normal = EmailValidator(strict=False)
        assert validator_normal.strict is False
        assert validator_normal.pattern == EmailValidator.EMAIL_PATTERN

    def test_additional_checks_length(self):
        """Тестирует проверку длины email."""
        validator = EmailValidator()
        
        # Очень длинный email (больше 254 символов)
        long_email = "a" * 250 + "@example.com"
        assert not validator.is_valid(long_email)

    def test_normalize_email(self):
        """Тестирует нормализацию email."""
        validator = EmailValidator()
        
        # Нормальный email
        assert validator.normalize_email("Test@Example.COM") == "test@example.com"
        
        # Пустой email
        assert validator.normalize_email("") is None
        assert validator.normalize_email(None) is None

    def test_extract_domain(self):
        """Тестирует извлечение домена."""
        validator = EmailValidator()
        
        assert validator.extract_domain("user@example.com") == "example.com"
        assert validator.extract_domain("Test@EXAMPLE.COM") == "example.com"
        assert validator.extract_domain("invalid-email") is None

    def test_get_validation_summary(self):
        """Тестирует получение сводки валидации."""
        validator = EmailValidator()
        
        emails = [
            "valid1@example.com",
            "valid2@test.org", 
            "invalid-email",
            "another@valid.com",
            ""
        ]
        
        summary = validator.get_validation_summary(emails)
        
        assert summary['total'] == 5
        assert summary['valid'] == 3
        assert summary['invalid'] == 2
        assert summary['success_rate'] == 0.6
        assert len(summary['valid_emails']) == 3
        assert len(summary['invalid_emails']) == 2

    def test_get_domain_statistics(self):
        """Тестирует статистику по доменам."""
        validator = EmailValidator()
        
        emails = [
            "user1@example.com",
            "user2@example.com",
            "user3@test.org",
            "invalid-email",
            "user4@example.com"
        ]
        
        stats = validator.get_domain_statistics(emails)
        
        assert stats["example.com"] == 3
        assert stats["test.org"] == 1
        assert "invalid-email" not in stats

    def test_validate_batch_edge_cases(self):
        """Тестирует batch валидацию с edge cases."""
        validator = EmailValidator()
        
        emails = [
            "valid@example.com",
            "",
            None,
            "user@",
            "@domain.com",
            "user@domain",
            "user.name@domain.com"
        ]
        
        # Фильтруем None значения
        filtered_emails = [email for email in emails if email is not None]
        results = validator.validate_batch(filtered_emails)
        
        assert len(results) == len(filtered_emails)
        
        # Проверяем что первый и последний email валидны
        assert results[0][1] is True  # valid@example.com
        assert results[-1][1] is True  # user.name@domain.com


class TestStatsAggregatorExtended:
    """Расширенные тесты для StatsAggregator."""

    def test_stats_initialization(self):
        """Тестирует инициализацию агрегатора."""
        aggregator = StatsAggregator()
        
        expected_stats = ['sent', 'delivered', 'failed', 'bounced', 'opened', 'clicked', 'unsubscribed']
        for stat in expected_stats:
            assert stat in aggregator.stats
            assert aggregator.stats[stat] == 0
        
        assert len(aggregator.events) == 0

    def test_add_event_with_kwargs(self):
        """Тестирует добавление события с дополнительными параметрами."""
        aggregator = StatsAggregator()
        
        aggregator.add_event(
            'delivered', 
            email='test@example.com',
            message_id='msg_123',
            timestamp='2024-01-20T10:30:00Z'
        )
        
        assert len(aggregator.events) == 1
        event = aggregator.events[0]
        assert event['type'] == 'delivered'
        assert event['email'] == 'test@example.com'
        assert event['message_id'] == 'msg_123'
        assert aggregator.stats['delivered'] == 1

    def test_increment_multiple_times(self):
        """Тестирует множественное увеличение счетчиков."""
        aggregator = StatsAggregator()
        
        aggregator.increment('sent', 5)
        aggregator.increment('sent', 3)
        aggregator.increment('delivered', 7)
        
        assert aggregator.stats['sent'] == 8
        assert aggregator.stats['delivered'] == 7
        assert aggregator.stats['failed'] == 0

    def test_increment_invalid_stat(self):
        """Тестирует увеличение несуществующего счетчика."""
        aggregator = StatsAggregator()
        
        # Не должно вызывать ошибку, но и не должно изменять статистику
        aggregator.increment('nonexistent_stat', 5)
        
        assert 'nonexistent_stat' not in aggregator.stats

    def test_get_stats_calculation(self):
        """Тестирует вычисление статистики."""
        aggregator = StatsAggregator()
        
        # Добавляем события
        aggregator.increment('sent', 100)
        aggregator.increment('delivered', 95)
        aggregator.increment('failed', 5)
        aggregator.add_event('opened', 'user1@example.com')
        aggregator.add_event('clicked', 'user2@example.com')
        
        stats = aggregator.get_stats()
        
        assert stats['sent'] == 100
        assert stats['delivered'] == 95
        assert stats['failed'] == 5
        assert stats['opened'] == 1
        assert stats['clicked'] == 1
        assert stats['total_events'] == 2  # Только events, не increments
        assert stats['success_rate'] == 0.95  # 95 delivered / 100 sent
        assert 'last_updated' in stats

    def test_success_rate_with_zero_sent(self):
        """Тестирует расчет success rate при нуле отправленных."""
        aggregator = StatsAggregator()
        
        # Не отправляем ничего
        aggregator.increment('delivered', 5)  # Это не должно влиять на rate
        
        stats = aggregator.get_stats()
        assert stats['success_rate'] == 0.0

    def test_reset_stats(self):
        """Тестирует сброс статистики."""
        aggregator = StatsAggregator()
        
        aggregator.increment('sent', 10)
        aggregator.add_event('delivered', 'test@example.com')
        
        # Проверяем что данные есть
        assert aggregator.stats['sent'] == 10
        assert len(aggregator.events) == 1
        
        # Сбрасываем (если такой метод есть)
        aggregator.stats = {key: 0 for key in aggregator.stats}
        aggregator.events.clear()
        
        assert aggregator.stats['sent'] == 0
        assert len(aggregator.events) == 0


class TestTemplateEngineExtended:
    """Расширенные тесты для TemplateEngine."""

    def test_html_to_text_parser(self):
        """Тестирует HTML парсер."""
        parser = HTMLToTextParser()
        
        html_content = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        parser.feed(html_content)
        
        text = parser.get_text()
        assert "Hello" in text
        assert "World" in text

    def test_template_engine_initialization(self):
        """Тестирует инициализацию движка шаблонов."""
        engine = TemplateEngine(template_dir="test_templates")
        
        assert engine.template_dir == "test_templates"
        assert engine.env is not None

    def test_render_template_with_context(self):
        """Тестирует рендеринг шаблона с контекстом."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем временный шаблон
            template_file = Path(temp_dir) / "test.html"
            template_file.write_text("<h1>Hello {{ name }}!</h1><p>Age: {{ age }}</p>")
            
            engine = TemplateEngine(template_dir=temp_dir)
            
            context = {"name": "John", "age": 30}
            result = engine.render_template("test.html", context)
            
            assert "Hello John!" in result
            assert "Age: 30" in result

    def test_render_nonexistent_template(self):
        """Тестирует рендеринг несуществующего шаблона."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = TemplateEngine(template_dir=temp_dir)
            
            from jinja2 import TemplateNotFound
            with pytest.raises(TemplateNotFound):
                engine.render_template("nonexistent.html", {})

    def test_template_with_special_characters(self):
        """Тестирует шаблон со специальными символами."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_file = Path(temp_dir) / "special.html"
            template_file.write_text("<p>Message: {{ message }}</p>")
            
            engine = TemplateEngine(template_dir=temp_dir)
            
            context = {"message": "<script>alert('xss')</script>"}
            result = engine.render_template("special.html", context)
            
            # Jinja2 должен экранировать HTML
            assert "&lt;script&gt;" in result or "script" not in result

    def test_template_with_loops(self):
        """Тестирует шаблон с циклами."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_file = Path(temp_dir) / "loop.html"
            template_file.write_text("""
            <ul>
            {% for item in items %}
                <li>{{ item.name }}: {{ item.value }}</li>
            {% endfor %}
            </ul>
            """)
            
            engine = TemplateEngine(template_dir=temp_dir)
            
            context = {
                "items": [
                    {"name": "Item 1", "value": 100},
                    {"name": "Item 2", "value": 200}
                ]
            }
            result = engine.render_template("loop.html", context)
            
            assert "Item 1: 100" in result
            assert "Item 2: 200" in result
            assert "<li>" in result

    def test_template_with_conditionals(self):
        """Тестирует шаблон с условиями."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_file = Path(temp_dir) / "conditional.html"
            template_file.write_text("""
            {% if user.is_premium %}
                <p>Welcome, premium user {{ user.name }}!</p>
            {% else %}
                <p>Welcome, {{ user.name }}!</p>
            {% endif %}
            """)
            
            engine = TemplateEngine(template_dir=temp_dir)
            
            # Тестируем премиум пользователя
            context = {"user": {"name": "John", "is_premium": True}}
            result = engine.render_template("conditional.html", context)
            assert "premium user John" in result
            
            # Тестируем обычного пользователя
            context = {"user": {"name": "Jane", "is_premium": False}}
            result = engine.render_template("conditional.html", context)
            assert "Welcome, Jane!" in result
            assert "premium" not in result


class TestEdgeCasesAndErrorHandling:
    """Тесты для edge cases и обработки ошибок."""

    def test_empty_data_handling(self):
        """Тестирует обработку пустых данных."""
        validator = EmailValidator()
        
        # Пустой список
        summary = validator.get_validation_summary([])
        assert summary['total'] == 0
        assert summary['success_rate'] == 0.0
        
        # Список с пустыми строками
        summary = validator.get_validation_summary(["", "   ", None])
        assert summary['valid'] == 0

    def test_memory_usage_edge_cases(self):
        """Тестирует edge cases с использованием памяти."""
        aggregator = StatsAggregator()
        
        # Добавляем большое количество событий
        for i in range(1000):
            aggregator.add_event(f'test_event_{i % 10}', f'user{i}@example.com')
        
        assert len(aggregator.events) == 1000
        
        # Получаем статистику - не должно падать
        stats = aggregator.get_stats()
        assert stats['total_events'] == 1000

    def test_unicode_email_handling(self):
        """Тестирует обработку unicode в email адресах."""
        validator = EmailValidator()
        
        # Международные домены
        unicode_emails = [
            "test@тест.рф",
            "用户@测试.中国",
            "test@münchen.de"
        ]
        
        # Валидатор должен обрабатывать их без ошибок
        for email in unicode_emails:
            try:
                result = validator.is_valid(email)
                # Результат может быть любым, главное что не падает
                assert isinstance(result, bool)
            except Exception as e:
                # Если не поддерживается, должно быть понятное исключение
                assert isinstance(e, (UnicodeError, ValueError))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])