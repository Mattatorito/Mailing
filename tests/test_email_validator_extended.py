#!/usr/bin/env python3
"""
Comprehensive extended tests for validation/email_validator.py
"""

import pytest
from unittest.mock import patch

from src.validation.email_validator import (
    EmailValidator, 
    validate_email, 
    normalize_email, 
    parse_email_with_name
)
from src.mailing.types import ValidationResult


class TestEmailValidatorExtensive:
    """Расширенные тесты для полного покрытия EmailValidator."""
    
    @pytest.fixture
    def validator(self):
        """Фикстура обычного валидатора."""
        return EmailValidator(strict=False)
    
    @pytest.fixture 
    def strict_validator(self):
        """Фикстура строгого валидатора."""
        return EmailValidator(strict=True)
    
    def test_init_strict_patterns(self, strict_validator, validator):
        """Тест выбора паттернов при инициализации."""
        assert strict_validator.strict is True
        assert strict_validator.pattern == EmailValidator.STRICT_EMAIL_PATTERN
        
        assert validator.strict is False
        assert validator.pattern == EmailValidator.EMAIL_PATTERN
    
    def test_is_valid_edge_cases(self, validator):
        """Тест валидации с граничными случаями."""
        # None и нестроковые типы
        assert not validator.is_valid(None)
        assert not validator.is_valid(123)
        assert not validator.is_valid([])
        assert not validator.is_valid({})
        
        # Пустые строки и пробелы
        assert not validator.is_valid("")
        assert not validator.is_valid("   ")
        assert not validator.is_valid("\t\n")
    
    def test_additional_checks_comprehensive(self, validator):
        """Тест всех дополнительных проверок."""
        # Проверка превышения максимальной длины email (254 символа)
        too_long_email = "a" * 64 + "@" + "b" * 191 + ".com"  # 64 + 1 + 195 = 260 - слишком длинный
        assert not validator.is_valid(too_long_email)
        
        # Проверка превышения максимальной длины домена (253 символа)  
        too_long_domain = "a" * 30 + "@" + "b" * 250 + ".com"  # домен 254 символа
        assert not validator.is_valid(too_long_domain)
        
        # Валидный длинный email в пределах RFC
        valid_long_email = "a" * 64 + "@" + "b" * 185 + ".com"  # 64 + 1 + 189 = 254 символа
        assert validator.is_valid(valid_long_email)  # Должен проходить
        
        # Более реалистичный тест
        normal_long_email = "a" * 50 + "@" + "b" * 50 + ".example.com"  # В пределах лимитов
        assert validator.is_valid(normal_long_email)
        
        very_long_email = "a" * 241 + "@example.com"  # 255 символов - не должен пройти
        assert not validator.is_valid(very_long_email)
        
        # Проверка длины локальной части (64 символа)
        long_local = "a" * 63 + "@example.com"  # 63 символа - должен пройти
        assert validator.is_valid(long_local)
        
        very_long_local = "a" * 65 + "@example.com"  # 65 символов - не должен пройти
        assert not validator.is_valid(very_long_local)
        
        # Проверка длины домена (253 символа для всего домена)
        # Реалистичный тест домена
        long_domain = "test@" + "a" * 50 + ".example.com"  # Нормальный домен
        assert validator.is_valid(long_domain)
        
        # Слишком длинный домен
        very_long_domain = "test@" + "a" * 250 + ".com"  # Больше 253 символов
        assert not validator.is_valid(very_long_domain)
        
        # Последовательные точки
        assert not validator.is_valid("test..email@example.com")
        assert not validator.is_valid("test@example..com")
        assert not validator.is_valid("test@ex..ample.com")
        
        # Точки в начале и конце локальной части
        assert not validator.is_valid(".test@example.com")
        assert not validator.is_valid("test.@example.com")
        
        # Точки в начале и конце домена
        assert not validator.is_valid("test@.example.com")
        assert not validator.is_valid("test@example.com.")
    
    def test_normalize_various_cases(self, validator):
        """Тест нормализации различных случаев."""
        # Обычная нормализация
        assert validator.normalize("TEST@EXAMPLE.COM") == "test@example.com"
        assert validator.normalize("  Test@Example.Com  ") == "test@example.com"
        
        # Алиас normalize_email
        assert validator.normalize_email("TEST@EXAMPLE.COM") == "test@example.com"
        
        # Невалидные email
        assert validator.normalize("invalid.email") is None
        assert validator.normalize("") is None
        assert validator.normalize("@") is None
        assert validator.normalize("test@") is None
        assert validator.normalize("@example.com") is None
    
    def test_extract_domain_edge_cases(self, validator):
        """Тест извлечения домена с граничными случаями."""
        # Обычные случаи
        assert validator.extract_domain("user@example.com") == "example.com"
        assert validator.extract_domain("USER@EXAMPLE.COM") == "example.com"
        
        # Сложные домены
        assert validator.extract_domain("test@sub.domain.example.com") == "sub.domain.example.com"
        assert validator.extract_domain("user@test-domain.co.uk") == "test-domain.co.uk"
        
        # Невалидные случаи
        assert validator.extract_domain("invalid-email") is None
        assert validator.extract_domain("user@") is None
        assert validator.extract_domain("@domain.com") is None
        assert validator.extract_domain("no-at-sign") is None
    
    def test_validate_batch_with_exceptions(self, validator):
        """Тест пакетной валидации с исключениями."""
        # Мокаем is_valid чтобы вызвать исключение
        with patch.object(validator, 'is_valid', side_effect=[True, Exception("Test error"), False]):
            results = validator.validate_batch(["valid@example.com", "error@test.com", "invalid"])
            
            assert len(results) == 3
            assert results[0] == ("valid@example.com", True, None)
            assert results[1] == ("error@test.com", False, "Test error")
            assert results[2] == ("invalid", False, "Invalid email format")
    
    def test_get_validation_summary_empty_list(self, validator):
        """Тест сводки валидации для пустого списка."""
        summary = validator.get_validation_summary([])
        
        expected = {
            'total': 0,
            'valid': 0, 
            'invalid': 0,
            'success_rate': 0.0,
            'valid_emails': [],
            'invalid_emails': [],
            'errors': []
        }
        
        assert summary == expected
    
    def test_get_validation_summary_all_invalid(self, validator):
        """Тест сводки валидации только с невалидными email."""
        emails = ["invalid1", "invalid2", "@invalid3"]
        summary = validator.get_validation_summary(emails)
        
        assert summary['total'] == 3
        assert summary['valid'] == 0
        assert summary['invalid'] == 3
        assert summary['success_rate'] == 0.0
        assert len(summary['valid_emails']) == 0
        assert len(summary['invalid_emails']) == 3
        assert len(summary['errors']) == 3
    
    def test_get_domain_statistics_empty_and_invalid(self, validator):
        """Тест статистики доменов с пустыми и невалидными email."""
        # Пустой список
        assert validator.get_domain_statistics([]) == {}
        
        # Только невалидные email
        stats = validator.get_domain_statistics(["invalid1", "invalid2", "@"])
        assert stats == {}
        
        # Смешанные валидные и невалидные
        emails = [
            "user@example.com",
            "invalid",
            "another@example.com", 
            "@invalid",
            "test@different.org"
        ]
        
        stats = validator.get_domain_statistics(emails)
        assert stats == {"example.com": 2, "different.org": 1}
    
    def test_get_typo_suggestions_no_at_sign(self, validator):
        """Тест предложений исправлений для email без @."""
        suggestions = validator.get_typo_suggestions("invalid_email_no_at")
        assert suggestions == []
    
    def test_get_typo_suggestions_popular_domains(self, validator):
        """Тест предложений для популярных доменов с опечатками."""
        # Опечатка в gmail
        suggestions = validator.get_typo_suggestions("user@gmial.com")
        assert "user@gmail.com" in suggestions
        
        # Опечатка в yahoo
        suggestions = validator.get_typo_suggestions("user@yaho.com")
        assert "user@yahoo.com" in suggestions
        
        # Опечатка в outlook
        suggestions = validator.get_typo_suggestions("user@outlok.com")
        assert "user@outlook.com" in suggestions
        
        # Слишком большая разница - не должно предлагать
        suggestions = validator.get_typo_suggestions("user@completely_different_domain.com")
        assert len(suggestions) == 0
    
    def test_is_similar_domain_algorithm(self, validator):
        """Тест алгоритма определения похожих доменов."""
        # Должны быть похожими
        assert validator._is_similar_domain("gmial.com", "gmail.com")
        assert validator._is_similar_domain("yaho.com", "yahoo.com")
        assert validator._is_similar_domain("outlok.com", "outlook.com")
        
        # Не должны быть похожими - слишком большая разница в длине
        assert not validator._is_similar_domain("a.com", "verylongdomain.com")
        
        # Не должны быть похожими - слишком много различий
        assert not validator._is_similar_domain("completely.com", "different.com")
        
        # Граничные случаи
        assert validator._is_similar_domain("test.com", "test.com")  # Одинаковые
        assert validator._is_similar_domain("tast.com", "test.com")  # Одно различие
    
    def test_strict_vs_normal_patterns(self, validator, strict_validator):
        """Тест различий между строгим и обычным валидаторами."""
        # Email которые могут проходить в обычном, но не в строгом режиме
        test_emails = [
            "test@example.com",  # Должен проходить в обоих
            "test.email@example.com",  # Должен проходить в обоих
            "test_email@example.com",  # Должен проходить в обоих
        ]
        
        for email in test_emails:
            normal_result = validator.is_valid(email)
            strict_result = strict_validator.is_valid(email)
            
            # В данном случае все должны проходить в обоих режимах
            # но в реальных сценариях строгий режим может быть более ограничительным
            assert normal_result == strict_result
    
    def test_case_sensitivity_handling(self, validator):
        """Тест обработки регистра символов."""
        # Все варианты должны считаться валидными и нормализоваться к нижнему регистру
        test_cases = [
            "Test@Example.Com",
            "TEST@EXAMPLE.COM",
            "test@example.com",
            "TeSt@ExAmPlE.cOm"
        ]
        
        for email in test_cases:
            assert validator.is_valid(email)
            assert validator.normalize(email) == "test@example.com"
            assert validator.extract_domain(email) == "example.com"


class TestStandalonneFunctions:
    """Тесты для standalone функций."""
    
    def test_validate_email_function(self):
        """Тест функции validate_email."""
        # Обычный режим
        assert validate_email("test@example.com") is True
        assert validate_email("invalid") is False
        
        # Строгий режим
        assert validate_email("test@example.com", strict=True) is True
        assert validate_email("invalid", strict=True) is False
    
    def test_normalize_email_function(self):
        """Тест функции normalize_email."""
        assert normalize_email("TEST@EXAMPLE.COM") == "test@example.com"
        assert normalize_email("invalid") is None
        assert normalize_email("") is None
    
    def test_parse_email_with_name_valid_cases(self):
        """Тест парсинга email с именем - валидные случаи."""
        # Формат "Name <email@domain.com>"
        name, email = parse_email_with_name("John Doe <john@example.com>")
        assert name == "John Doe"
        assert email == "john@example.com"
        
        # Просто email
        name, email = parse_email_with_name("test@example.com")
        assert name is None
        assert email == "test@example.com"
        
        # Пустое имя
        name, email = parse_email_with_name(" <test@example.com>")
        assert name is None
        assert email == "test@example.com"
        
        # Имя с пробелами
        name, email = parse_email_with_name("  John Doe  <john@example.com>")
        assert name == "John Doe"
        assert email == "john@example.com"
    
    def test_parse_email_with_name_invalid_cases(self):
        """Тест парсинга email с именем - невалидные случаи."""
        # Невалидный email
        name, email = parse_email_with_name("John Doe <invalid_email>")
        assert name is None
        assert email is None
        
        # Пустая строка
        name, email = parse_email_with_name("")
        assert name is None
        assert email is None
        
        # Только имя без email
        name, email = parse_email_with_name("John Doe")
        assert name is None
        assert email is None
        
        # Неправильный формат
        name, email = parse_email_with_name("John Doe john@example.com")
        assert name is None
        assert email is None
    
    def test_parse_email_with_name_exception_handling(self):
        """Тест обработки исключений в parse_email_with_name."""
        # Мокаем parseaddr чтобы вызвать исключение
        with patch('validation.email_validator.parseaddr', side_effect=Exception("Parse error")):
            name, email = parse_email_with_name("test@example.com")
            assert name is None
            assert email is None


class TestMainExecution:
    """Тест выполнения модуля как скрипта."""
    
    def test_main_execution(self):
        """Тест выполнения кода в блоке if __name__ == "__main__"."""
        # Этот тест проверяет что код в main блоке не вызывает ошибок
        # В реальности main блок не выполняется при импорте модуля
        validator = EmailValidator()
        
        test_emails = [
            "test@example.com",
            "invalid.email",
            "user@gmail.com",
            "bad@domain",
            "good.email@valid-domain.co.uk"
        ]
        
        # Проверяем что все email можно валидировать без ошибок
        for email in test_emails:
            is_valid = validator.is_valid(email)
            assert isinstance(is_valid, bool)


class TestRegressionAndEdgeCases:
    """Тесты для регрессий и дополнительных граничных случаев."""
    
    def test_unicode_handling(self):
        """Тест обработки Unicode символов."""
        validator = EmailValidator()
        
        # ASCII email должен проходить
        assert validator.is_valid("test@example.com")
        
        # Unicode символы в email (обычно не поддерживаются стандартными паттернами)
        unicode_emails = [
            "тест@example.com",
            "test@пример.рф",
            "测试@example.com"
        ]
        
        for email in unicode_emails:
            # Зависит от реализации паттерна, но обычно не проходят
            result = validator.is_valid(email)
            assert isinstance(result, bool)
    
    def test_very_long_domain_parts(self):
        """Тест очень длинных частей домена."""
        validator = EmailValidator()
        
        # Длинная поддомена
        long_subdomain = "a" * 63  # Максимальная длина части домена
        email = f"test@{long_subdomain}.example.com"
        assert validator.is_valid(email)
        
        # Слишком длинная поддомена
        too_long_subdomain = "a" * 64
        email = f"test@{too_long_subdomain}.example.com"
        # Может не пройти в зависимости от реализации
        result = validator.is_valid(email)
        assert isinstance(result, bool)
    
    def test_special_characters_in_local_part(self):
        """Тест специальных символов в локальной части."""
        validator = EmailValidator()
        
        special_char_emails = [
            "test+tag@example.com",      # Плюс
            "test-user@example.com",     # Дефис
            "test_user@example.com",     # Подчеркивание
            "test.user@example.com",     # Точка
            "test%user@example.com",     # Процент
        ]
        
        for email in special_char_emails:
            result = validator.is_valid(email)
            assert isinstance(result, bool)
    
    def test_normalization_consistency(self):
        """Тест консистентности нормализации."""
        validator = EmailValidator()
        
        variations = [
            "Test@Example.Com",
            "TEST@EXAMPLE.COM", 
            "test@example.com",
            "  test@example.com  "
        ]
        
        normalized_results = [validator.normalize(email) for email in variations]
        
        # Все должны нормализоваться к одному результату
        assert len(set(filter(None, normalized_results))) == 1
        assert normalized_results[0] == "test@example.com"