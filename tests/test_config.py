#!/usr/bin/env python3

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from src.mailing.config import Settings, settings


@patch.dict(os.environ, {}, clear=True)  # Очищаем переменные окружения для теста
def test_settings_initialization():
    """Тестирует инициализацию настроек."""
    # Создаем новый экземпляр настроек
    test_settings = Settings()
    
    # Проверяем значения по умолчанию
    assert test_settings.resend_api_key == "your_api_key"
    assert test_settings.sqlite_db_path == "test_mailing.sqlite3"
    assert test_settings.templates_dir == "samples"
    assert test_settings.concurrency == 5
    assert test_settings.daily_limit == 100


@patch.dict(os.environ, {
    'RESEND_API_KEY': 'test_key_123',
    'SQLITE_DB_PATH': 'custom_test.db',
    'TEMPLATES_DIR': 'custom_templates',
    'CONCURRENCY': '10',
    'DAILY_LIMIT': '500'
})
def test_settings_from_environment():
    """Тестирует загрузку настроек из переменных окружения."""
    test_settings = Settings()
    
    assert test_settings.resend_api_key == "test_key_123"
    assert test_settings.sqlite_db_path == "custom_test.db"
    assert test_settings.templates_dir == "custom_templates"
    assert test_settings.concurrency == 10
    assert test_settings.daily_limit == 500


@patch.dict(os.environ, {}, clear=True)  # Очищаем переменные окружения
def test_settings_from_env_file():
    """Тестирует загрузку настроек из .env файла."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
RESEND_API_KEY=test_key_secure
SQLITE_DB_PATH=test_db.sqlite3
TEMPLATES_DIR=test_templates
CONCURRENCY=15
DAILY_LIMIT=1000
""")
        f.flush()
        env_file = f.name
    
    try:
        # Загружаем переменные из файла
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        # Создаем настройки - они должны загрузиться из переменных окружения
        test_settings = Settings()
        
        # Проверяем что значения загрузились
        assert test_settings.resend_api_key == "test_key_secure"
        assert test_settings.sqlite_db_path == "test_db.sqlite3"
        assert test_settings.templates_dir == "test_templates"
        assert test_settings.concurrency == 15
        assert test_settings.daily_limit == 1000
    finally:
        Path(env_file).unlink(missing_ok=True)


def test_settings_validation():
    """Тестирует валидацию настроек."""
    # Создаем настройки с некорректными значениями
    with patch.dict(os.environ, {'CONCURRENCY': '-1', 'DAILY_LIMIT': '0'}):
        with pytest.raises(ValueError):
            Settings()


def test_global_settings_instance():
    """Тестирует глобальный экземпляр настроек."""
    # Проверяем что settings это экземпляр Settings
    assert isinstance(settings, Settings)
    
    # Проверяем что у него есть все необходимые атрибуты
    assert hasattr(settings, 'resend_api_key')
    assert hasattr(settings, 'sqlite_db_path')
    assert hasattr(settings, 'templates_dir')
    assert hasattr(settings, 'concurrency')
    assert hasattr(settings, 'daily_limit')


@patch.dict(os.environ, {'RESEND_API_KEY': ''})
def test_empty_api_key():
    """Тестирует поведение с пустым API ключом."""
    test_settings = Settings()
    assert test_settings.resend_api_key == ""


def test_settings_repr():
    """Тестирует строковое представление настроек."""
    test_settings = Settings()
    repr_str = repr(test_settings)
    assert 'Settings' in repr_str
    # API ключ не должен отображаться в repr для безопасности
    assert 'your_api_key' not in repr_str or '***' in repr_str