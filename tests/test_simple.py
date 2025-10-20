"""
Простой тест для проверки основной функциональности
"""

import pytest
import os
import sys
import tempfile

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_basic_imports():
    """Тест базовых импортов"""
    try:
        from mailing import config
        from templating import engine
        from persistence import db
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import: {e}")


def test_database_connection():
    """Тест подключения к базе данных"""
    try:
        from persistence.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        assert result[0] == 1
    except Exception as e:
        pytest.fail(f"Database test failed: {e}")


def test_template_engine():
    """Тест работы шаблонизатора"""
    try:
        from templating.engine import TemplateEngine
        engine = TemplateEngine()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("Hello {{ name }}!")
            template_path = f.name
        
        result = engine.render_string("Hello {{ name }}!", {"name": "World"})
        assert result == "Hello World!"
        
        os.unlink(template_path)
        
    except Exception as e:
        pytest.fail(f"Template engine test failed: {e}")


def test_config_loading():
    """Тест загрузки конфигурации"""
    try:
        from mailing.config import Settings
        settings = Settings()
        # Просто проверяем что объект создался
        assert hasattr(settings, 'resend_api_key')
    except Exception as e:
        pytest.fail(f"Config test failed: {e}")


def test_email_validation():
    """Тест валидации email"""
    try:
        from validation.email_validator import EmailValidator
        validator = EmailValidator()
        
        assert validator.is_valid("test@example.com") is True
        assert validator.is_valid("invalid-email") is False
        
    except Exception as e:
        pytest.fail(f"Email validation test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
