#!/usr/bin/env python3
"""
Отдельные тесты для валидации конфигурации.
Разделены для лучшего покрытия и читаемости.
"""

import pytest
import os
from unittest.mock import patch
from src.mailing.config import Settings


class TestConfigValidation:
    """Тесты валидации конфигурационных значений."""

    @patch.dict(os.environ, {'CONCURRENCY': '0'})
    def test_concurrency_validation_zero(self):
        """Тестирует валидацию concurrency = 0."""
        with pytest.raises(ValueError, match="concurrency должно быть больше 0"):
            Settings()

    @patch.dict(os.environ, {'CONCURRENCY': '-1'})
    def test_concurrency_validation_negative(self):
        """Тестирует валидацию отрицательного concurrency."""
        with pytest.raises(ValueError, match="concurrency должно быть больше 0"):
            Settings()

    @patch.dict(os.environ, {'DAILY_LIMIT': '0'})
    def test_daily_limit_validation_zero(self):
        """Тестирует валидацию daily_limit = 0."""
        with pytest.raises(ValueError, match="daily_limit должно быть больше 0"):
            Settings()

    @patch.dict(os.environ, {'DAILY_LIMIT': '-10'})
    def test_daily_limit_validation_negative(self):
        """Тестирует валидацию отрицательного daily_limit."""
        with pytest.raises(ValueError, match="daily_limit должно быть больше 0"):
            Settings()

    @patch.dict(os.environ, {'RATE_LIMIT_PER_MINUTE': '0'})
    def test_rate_limit_validation_zero(self):
        """Тестирует валидацию rate_limit_per_minute = 0."""
        with pytest.raises(ValueError, match="rate_limit_per_minute должно быть больше 0"):
            Settings()

    @patch.dict(os.environ, {'MAX_RETRIES': '-1'})
    def test_max_retries_validation_negative(self):
        """Тестирует валидацию отрицательного max_retries."""
        with pytest.raises(ValueError, match="max_retries не может быть отрицательным"):
            Settings()

    @patch.dict(os.environ, {'SMTP_TIMEOUT': '0'})
    def test_smtp_timeout_validation_zero(self):
        """Тестирует валидацию smtp_timeout = 0."""
        with pytest.raises(ValueError, match="smtp_timeout должно быть больше 0"):
            Settings()

    @patch.dict(os.environ, {'CONCURRENCY': 'invalid'})
    def test_concurrency_invalid_value(self):
        """Тестирует валидацию невалидного значения concurrency."""
        with pytest.raises(ValueError):
            Settings()

    @patch.dict(os.environ, {'DAILY_LIMIT': 'not_a_number'})
    def test_daily_limit_invalid_value(self):
        """Тестирует валидацию невалидного значения daily_limit."""
        with pytest.raises(ValueError):
            Settings()


class TestConfigEdgeCases:
    """Тесты граничных случаев конфигурации."""

    @patch.dict(os.environ, {'MAX_RETRIES': '0'})
    def test_max_retries_zero_allowed(self):
        """Тестирует что max_retries = 0 разрешен."""
        settings = Settings()
        assert settings.max_retries == 0

    @patch.dict(os.environ, {'CONCURRENCY': '1'})
    def test_concurrency_minimum_valid(self):
        """Тестирует минимальное валидное значение concurrency."""
        settings = Settings()
        assert settings.concurrency == 1

    @patch.dict(os.environ, {'DAILY_LIMIT': '1'})
    def test_daily_limit_minimum_valid(self):
        """Тестирует минимальное валидное значение daily_limit."""
        settings = Settings()
        assert settings.daily_limit == 1

    @patch.dict(os.environ, {'RATE_LIMIT_PER_MINUTE': '1'})
    def test_rate_limit_minimum_valid(self):
        """Тестирует минимальное валидное значение rate_limit_per_minute."""
        settings = Settings()
        assert settings.rate_limit_per_minute == 1

    @patch.dict(os.environ, {'SMTP_TIMEOUT': '1'})
    def test_smtp_timeout_minimum_valid(self):
        """Тестирует минимальное валидное значение smtp_timeout."""
        settings = Settings()
        assert settings.smtp_timeout == 1


class TestConfigStringFields:
    """Тесты для строковых полей конфигурации."""

    @patch.dict(os.environ, {'RESEND_API_KEY': ''})
    def test_empty_api_key(self):
        """Тестирует поведение с пустым API ключом."""
        settings = Settings()
        assert settings.resend_api_key == ""

    @patch.dict(os.environ, {'SQLITE_DB_PATH': ''})
    def test_empty_db_path(self):
        """Тестирует поведение с пустым путем к БД."""
        settings = Settings()
        assert settings.sqlite_db_path == ""

    @patch.dict(os.environ, {'TEMPLATES_DIR': ''})
    def test_empty_templates_dir(self):
        """Тестирует поведение с пустой директорией шаблонов."""
        settings = Settings()
        assert settings.templates_dir == ""

    @patch.dict(os.environ, {
        'RESEND_API_KEY': 'sk_' + 'x' * 100,  # Очень длинный ключ
        'SQLITE_DB_PATH': 'very/long/path/to/database/file.sqlite3',
        'TEMPLATES_DIR': 'very/long/path/to/templates/directory'
    })
    def test_long_string_values(self):
        """Тестирует поведение с длинными строковыми значениями."""
        settings = Settings()
        assert len(settings.resend_api_key) > 100
        assert 'very/long/path' in settings.sqlite_db_path
        assert 'very/long/path' in settings.templates_dir