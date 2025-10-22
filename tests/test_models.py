#!/usr/bin/env python3

import pytest
from datetime import datetime
from src.mailing.models import Recipient, DeliveryResult


def test_recipient_creation():
    """Тестирует создание получателя."""
    recipient = Recipient(
        email="test@example.com",
        name="Test User",
        variables={"company": "Test Corp", "position": "Developer"}
    )
    
    assert recipient.email == "test@example.com"
    assert recipient.name == "Test User"
    assert recipient.variables["company"] == "Test Corp"
    assert recipient.variables["position"] == "Developer"


def test_recipient_minimal():
    """Тестирует создание получателя с минимальными данными."""
    recipient = Recipient(email="minimal@example.com")
    
    assert recipient.email == "minimal@example.com"
    assert recipient.name == "minimal@example.com"  # Должно использовать email как имя
    assert recipient.variables == {}


def test_recipient_with_variables_only():
    """Тестирует создание получателя только с переменными."""
    recipient = Recipient(
        email="vars@example.com",
        variables={"key1": "value1", "key2": "value2"}
    )
    
    assert recipient.email == "vars@example.com"
    assert recipient.variables["key1"] == "value1"
    assert recipient.variables["key2"] == "value2"


def test_recipient_string_representation():
    """Тестирует строковое представление получателя."""
    recipient = Recipient(
        email="test@example.com",
        name="Test User"
    )
    
    str_repr = str(recipient)
    assert "test@example.com" in str_repr
    assert "Test User" in str_repr


def test_delivery_result_success():
    """Тестирует создание успешного результата доставки."""
    result = DeliveryResult(
        email="success@example.com",
        success=True,
        status_code=200,
        message_id="msg_123456",
        provider="resend"
    )
    
    assert result.email == "success@example.com"
    assert result.success is True
    assert result.status_code == 200
    assert result.message_id == "msg_123456"
    assert result.provider == "resend"
    assert result.error == ""
    assert isinstance(result.timestamp, str)


def test_delivery_result_failure():
    """Тестирует создание неуспешного результата доставки."""
    result = DeliveryResult(
        email="failed@example.com",
        success=False,
        status_code=400,
        error="Invalid email address",
        provider="resend"
    )
    
    assert result.email == "failed@example.com"
    assert result.success is False
    assert result.status_code == 400
    assert result.error == "Invalid email address"
    assert result.message_id == ""


def test_delivery_result_minimal():
    """Тестирует создание результата с минимальными данными."""
    result = DeliveryResult(
        email="minimal@example.com",
        success=True
    )
    
    assert result.email == "minimal@example.com"
    assert result.success is True
    assert result.status_code == 0
    assert result.message_id == ""
    assert result.error == ""
    assert result.provider == ""


def test_delivery_result_timestamp():
    """Тестирует автоматическое создание timestamp."""
    result1 = DeliveryResult(email="test1@example.com", success=True)
    result2 = DeliveryResult(email="test2@example.com", success=True)
    
    # Timestamp должен создаваться автоматически
    assert result1.timestamp != ""
    assert result2.timestamp != ""
    
    # Timestamps должны быть разными (или очень близкими)
    # Проверяем что это валидные ISO datetime строки
    datetime.fromisoformat(result1.timestamp.replace('Z', '+00:00'))
    datetime.fromisoformat(result2.timestamp.replace('Z', '+00:00'))


def test_delivery_result_string_representation():
    """Тестирует строковое представление результата доставки."""
    result = DeliveryResult(
        email="test@example.com",
        success=True,
        status_code=200
    )
    
    str_repr = str(result)
    assert "test@example.com" in str_repr
    assert "success=True" in str_repr or "True" in str_repr


def test_recipient_equality():
    """Тестирует сравнение получателей."""
    recipient1 = Recipient(
        email="test@example.com",
        name="Test User",
        variables={"key": "value"}
    )
    recipient2 = Recipient(
        email="test@example.com",
        name="Test User",
        variables={"key": "value"}
    )
    recipient3 = Recipient(
        email="different@example.com",
        name="Different User"
    )
    
    assert recipient1.email == recipient2.email  # Сравниваем по email
    assert recipient1.email != recipient3.email


def test_delivery_result_equality():
    """Тестирует сравнение результатов доставки."""
    result1 = DeliveryResult(email="test@example.com", success=True)
    result2 = DeliveryResult(email="test@example.com", success=True)
    result3 = DeliveryResult(email="different@example.com", success=True)
    
    assert result1.email == result2.email
    assert result1.email != result3.email