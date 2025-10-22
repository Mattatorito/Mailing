#!/usr/bin/env python3

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch
from src.persistence.repository import DeliveryRepository, SuppressionRepository
from src.mailing.models import DeliveryResult


@pytest.fixture
def temp_db():
    """Создает временную базу данных для тестов."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
        db_path = f.name
        
    yield db_path
    
    # Удаляем временный файл
    Path(db_path).unlink(missing_ok=True)


def test_delivery_repository_init(temp_db):
    """Тестирует инициализацию репозитория доставки."""
    repo = DeliveryRepository(temp_db)
    
    # Проверяем что база данных создалась
    assert Path(temp_db).exists()
    
    # Проверяем что таблица создалась
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='deliveries'"
        )
        assert cursor.fetchone() is not None


def test_save_delivery_success(temp_db):
    """Тестирует сохранение успешной доставки."""
    repo = DeliveryRepository(temp_db)
    
    result = DeliveryResult(
        email="test@example.com",
        success=True,
        status_code=200,
        message_id="msg_123",
        provider="resend"
    )
    
    repo.save_delivery(result)
    
    # Проверяем что запись сохранилась
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute("SELECT * FROM deliveries WHERE email = ?", ("test@example.com",))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == "test@example.com"  # email
        assert row[2] == 1  # success (True)
        assert row[3] == 200  # status_code
        assert row[4] == "msg_123"  # message_id


def test_save_delivery_failure(temp_db):
    """Тестирует сохранение неуспешной доставки."""
    repo = DeliveryRepository(temp_db)
    
    result = DeliveryResult(
        email="failed@example.com",
        success=False,
        status_code=400,
        error="Invalid email",
        provider="resend"
    )
    
    repo.save_delivery(result)
    
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute("SELECT * FROM deliveries WHERE email = ?", ("failed@example.com",))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == "failed@example.com"
        assert row[2] == 0  # success (False)
        assert row[3] == 400
        assert "Invalid email" in row[5]  # error


def test_get_recent_deliveries(temp_db):
    """Тестирует получение недавних доставок."""
    repo = DeliveryRepository(temp_db)
    
    # Сохраняем несколько доставок
    results = [
        DeliveryResult(email=f"user{i}@example.com", success=True)
        for i in range(5)
    ]
    
    for result in results:
        repo.save_delivery(result)
    
    recent = repo.get_recent_deliveries(3)
    
    assert len(recent) == 3
    # Проверяем что все записи присутствуют и корректны
    emails = [r['email'] for r in recent]
    assert all('user' in email for email in emails)
    assert all('@example.com' in email for email in emails)


def test_get_delivery_stats(temp_db):
    """Тестирует получение статистики доставок."""
    repo = DeliveryRepository(temp_db)
    
    # Добавляем смешанные результаты
    success_results = [
        DeliveryResult(email=f"success{i}@example.com", success=True)
        for i in range(3)
    ]
    fail_results = [
        DeliveryResult(email=f"fail{i}@example.com", success=False)
        for i in range(2)
    ]
    
    for result in success_results + fail_results:
        repo.save_delivery(result)
    
    stats = repo.get_delivery_stats()
    
    assert stats['total'] == 5
    assert stats['successful'] == 3
    assert stats['failed'] == 2
    assert stats['success_rate'] == 60.0


def test_get_delivery_stats_empty(temp_db):
    """Тестирует статистику для пустой базы."""
    repo = DeliveryRepository(temp_db)
    
    stats = repo.get_delivery_stats()
    
    assert stats['total'] == 0
    assert stats['successful'] == 0
    assert stats['failed'] == 0
    assert stats['success_rate'] == 0.0


def test_get_deliveries_by_email(temp_db):
    """Тестирует получение доставок по email."""
    repo = DeliveryRepository(temp_db)
    
    # Добавляем несколько доставок для одного email
    email = "multi@example.com"
    results = [
        DeliveryResult(email=email, success=True, status_code=200),
        DeliveryResult(email=email, success=False, status_code=400),
        DeliveryResult(email="other@example.com", success=True)
    ]
    
    for result in results:
        repo.save_delivery(result)
    
    deliveries = repo.get_deliveries_by_email(email)
    
    assert len(deliveries) == 2
    assert all(d['email'] == email for d in deliveries)


def test_clear_old_deliveries(temp_db):
    """Тестирует очистку старых доставок."""
    repo = DeliveryRepository(temp_db)
    
    # Добавляем несколько доставок
    for i in range(10):
        result = DeliveryResult(email=f"user{i}@example.com", success=True)
        repo.save_delivery(result)
    
    # Очищаем старые (оставляем только 5 последних)
    repo.clear_old_deliveries(keep_recent=5)
    
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM deliveries")
        count = cursor.fetchone()[0]
        
        assert count == 5


def test_suppression_repository_init():
    """Тестирует инициализацию репозитория подавлений."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
        db_path = f.name
    
    try:
        repo = SuppressionRepository(db_path)
        
        # Проверяем что таблицы создались
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='suppressions'"
            )
            assert cursor.fetchone() is not None
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_add_suppression():
    """Тестирует добавление подавления."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
        db_path = f.name
    
    try:
        repo = SuppressionRepository(db_path)
        
        repo.add_suppression("blocked@example.com", "bounce", "Hard bounce")
        
        # Проверяем что запись добавилась
        assert repo.is_suppressed("blocked@example.com") == True
        assert repo.is_unsubscribed("blocked@example.com") == False
        
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_add_unsubscribe():
    """Тестирует добавление отписки."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
        db_path = f.name
    
    try:
        repo = SuppressionRepository(db_path)
        
        repo.add_unsubscribe("unsubscribed@example.com")
        
        assert repo.is_unsubscribed("unsubscribed@example.com") == True
        assert repo.is_suppressed("unsubscribed@example.com") == False
        
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_remove_suppression():
    """Тестирует удаление подавления."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
        db_path = f.name
    
    try:
        repo = SuppressionRepository(db_path)
        
        # Добавляем подавление
        repo.add_suppression("temp@example.com", "bounce", "Test")
        assert repo.is_suppressed("temp@example.com") == True
        
        # Удаляем
        repo.remove_suppression("temp@example.com")
        assert repo.is_suppressed("temp@example.com") == False
        
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_get_all_suppressions():
    """Тестирует получение всех подавлений."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
        db_path = f.name
    
    try:
        repo = SuppressionRepository(db_path)
        
        # Добавляем несколько подавлений
        emails = ["bounce1@example.com", "bounce2@example.com", "unsub@example.com"]
        repo.add_suppression(emails[0], "bounce", "Hard bounce")
        repo.add_suppression(emails[1], "spam", "Spam complaint")
        repo.add_unsubscribe(emails[2])
        
        all_suppressions = repo.get_all_suppressions()
        
        assert len(all_suppressions) >= 3  # Может быть больше из-за unsubscribe
        
        # Проверяем что наши email есть в списке
        suppressed_emails = [s['email'] for s in all_suppressions]
        for email in emails:
            assert email in suppressed_emails
            
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_repository_migration(temp_db):
    """Тестирует миграцию базы данных."""
    # Создаем базу со старой схемой (без timestamp и provider)
    with sqlite3.connect(temp_db) as conn:
        conn.execute("""
            CREATE TABLE deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                status_code INTEGER,
                message_id TEXT,
                error TEXT
            )
        """)
        conn.commit()
    
    # Инициализируем репозиторий (должен выполнить миграцию)
    repo = DeliveryRepository(temp_db)
    
    # Проверяем что новые колонки добавились
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute("PRAGMA table_info(deliveries)")
        columns = [row[1] for row in cursor.fetchall()]
        
        assert 'timestamp' in columns
        assert 'provider' in columns


@patch('persistence.repository.settings')
def test_repository_uses_settings(mock_settings, temp_db):
    """Тестирует что репозиторий использует настройки."""
    mock_settings.sqlite_db_path = temp_db
    
    # Создаем репозиторий без указания пути (должен использовать settings)
    repo = DeliveryRepository()
    
    assert repo.db_path == temp_db