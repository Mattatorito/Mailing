#!/usr/bin/env python3

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.stats.aggregator import StatsAggregator
from src.mailing.models import DeliveryResult


def test_stats_aggregator_initialization():
    """Тестирует инициализацию агрегатора статистики."""
    stats = StatsAggregator()
    
    # Проверяем начальные значения
    assert stats.stats['sent'] == 0
    assert stats.stats['delivered'] == 0
    assert stats.stats['failed'] == 0
    assert stats.stats['bounced'] == 0
    assert stats.stats['opened'] == 0
    assert stats.stats['clicked'] == 0
    assert stats.stats['unsubscribed'] == 0
    assert len(stats.events) == 0


def test_add_event():
    """Тестирует добавление событий."""
    stats = StatsAggregator()
    
    stats.add_event("sent", "test@example.com", subject="Test Subject")
    
    assert len(stats.events) == 1
    assert stats.stats['sent'] == 1
    
    event = stats.events[0]
    assert event['type'] == 'sent'
    assert event['email'] == 'test@example.com'
    assert event['subject'] == 'Test Subject'
    assert 'timestamp' in event


def test_add_event_without_email():
    """Тестирует добавление событий без email."""
    stats = StatsAggregator()
    
    stats.add_event("delivered")
    
    assert len(stats.events) == 1
    assert stats.stats['delivered'] == 1
    
    event = stats.events[0]
    assert event['email'] == ""


def test_increment():
    """Тестирует увеличение счетчиков."""
    stats = StatsAggregator()
    
    stats.increment('sent', 5)
    stats.increment('delivered', 3)
    stats.increment('failed')  # По умолчанию +1
    
    assert stats.stats['sent'] == 5
    assert stats.stats['delivered'] == 3
    assert stats.stats['failed'] == 1


def test_increment_unknown_stat():
    """Тестирует увеличение несуществующего счетчика."""
    stats = StatsAggregator()
    
    # Не должно выбрасывать исключение
    stats.increment('unknown_stat', 10)
    
    # Значение не должно измениться
    assert 'unknown_stat' not in stats.stats


def test_get_stats():
    """Тестирует получение статистики."""
    stats = StatsAggregator()
    
    # Добавляем некоторые события
    stats.add_event('sent', 'user1@example.com')
    stats.add_event('sent', 'user2@example.com')
    stats.add_event('delivered', 'user1@example.com')
    
    result = stats.get_stats()
    
    assert result['sent'] == 2
    assert result['delivered'] == 1
    assert result['failed'] == 0
    assert result['total_events'] == 3
    assert result['success_rate'] == 0.5  # 1 delivered из 2 sent (как доля)
    assert 'last_updated' in result


def test_snapshot_alias():
    """Тестирует что snapshot это алиас для get_stats."""
    stats = StatsAggregator()
    stats.add_event('sent', 'test@example.com')
    
    get_stats_result = stats.get_stats()
    snapshot_result = stats.snapshot()
    
    # Сравниваем все поля кроме timestamp, так как он генерируется каждый раз
    for key in get_stats_result:
        if key != 'last_updated':
            assert get_stats_result[key] == snapshot_result[key]
    
    # Проверяем что timestamp есть в обоих результатах
    assert 'last_updated' in get_stats_result
    assert 'last_updated' in snapshot_result


def test_add_delivery_result_success():
    """Тестирует добавление успешного результата доставки."""
    stats = StatsAggregator()
    
    result = DeliveryResult(
        email="success@example.com",
        success=True,
        status_code=200,
        provider="resend"
    )
    
    stats.add(result)
    
    assert stats.stats['sent'] == 1
    assert stats.stats['delivered'] == 1
    assert stats.stats['failed'] == 0
    assert len(stats.events) == 1
    
    event = stats.events[0]
    assert event['type'] == 'delivery'
    assert event['email'] == 'success@example.com'
    assert event['success'] == True
    assert event['status_code'] == 200


def test_add_delivery_result_failure():
    """Тестирует добавление неуспешного результата доставки."""
    stats = StatsAggregator()
    
    result = DeliveryResult(
        email="failed@example.com",
        success=False,
        status_code=400,
        error="Invalid email"
    )
    
    stats.add(result)
    
    assert stats.stats['sent'] == 1
    assert stats.stats['delivered'] == 0
    assert stats.stats['failed'] == 1


def test_success_rate_calculation():
    """Тестирует вычисление процента успешности."""
    stats = StatsAggregator()
    
    # Добавляем события
    stats.increment('sent', 10)
    stats.increment('delivered', 8)
    
    success_rate = stats._calculate_success_rate()
    assert success_rate == 0.8


def test_success_rate_no_sent():
    """Тестирует вычисление процента при отсутствии отправок."""
    stats = StatsAggregator()
    
    success_rate = stats._calculate_success_rate()
    assert success_rate == 0.0


def test_get_events_by_type():
    """Тестирует получение событий по типу."""
    stats = StatsAggregator()
    
    stats.add_event('sent', 'user1@example.com')
    stats.add_event('delivered', 'user1@example.com')
    stats.add_event('sent', 'user2@example.com')
    stats.add_event('failed', 'user3@example.com')
    
    sent_events = stats.get_events_by_type('sent')
    delivered_events = stats.get_events_by_type('delivered')
    
    assert len(sent_events) == 2
    assert len(delivered_events) == 1
    assert all(event['type'] == 'sent' for event in sent_events)
    assert delivered_events[0]['email'] == 'user1@example.com'


def test_get_events_by_timeframe():
    """Тестирует получение событий за временной период."""
    stats = StatsAggregator()
    
    # Мокаем datetime для контроля времени
    with patch('stats.aggregator.datetime') as mock_datetime:
        # Текущее время
        now = datetime(2023, 10, 21, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_datetime.fromisoformat = datetime.fromisoformat  # Не мокаем fromisoformat
        
        # Добавляем события с разным временем
        old_time = now - timedelta(hours=25)  # Старше 24 часов
        recent_time = now - timedelta(hours=2)   # Последние 24 часа
        
        # Устанавливаем события с правильными строковыми timestamps
        stats.events = [
            {'type': 'sent', 'timestamp': old_time.isoformat()},
            {'type': 'sent', 'timestamp': recent_time.isoformat()},
            {'type': 'delivered', 'timestamp': now.isoformat()}
        ]
        
        recent_events = stats.get_events_by_timeframe(24)
        
        # Должны получить только 2 недавних события
        assert len(recent_events) == 2
        assert recent_events[0]['type'] == 'sent'
        assert recent_events[1]['type'] == 'delivered'


def test_export_stats():
    """Тестирует экспорт статистики в JSON."""
    stats = StatsAggregator()
    
    stats.add_event('sent', 'test@example.com')
    stats.add_event('delivered', 'test@example.com')
    
    exported = stats.export_stats()
    
    # Проверяем что это валидный JSON
    parsed = json.loads(exported)
    
    assert parsed['sent'] == 1
    assert parsed['delivered'] == 1
    assert parsed['total_events'] == 2
    assert 'success_rate' in parsed
    assert 'last_updated' in parsed


def test_reset():
    """Тестирует сброс статистики."""
    stats = StatsAggregator()
    
    # Добавляем данные
    stats.add_event('sent', 'test@example.com')
    stats.add_event('delivered', 'test@example.com')
    stats.increment('failed', 5)
    
    # Проверяем что данные есть
    assert stats.stats['sent'] == 1
    assert stats.stats['failed'] == 5
    assert len(stats.events) == 2
    
    # Сбрасываем
    stats.reset()
    
    # Проверяем что все сброшено
    assert stats.stats['sent'] == 0
    assert stats.stats['delivered'] == 0
    assert stats.stats['failed'] == 0
    assert len(stats.events) == 0


def test_multiple_add_calls():
    """Тестирует множественные вызовы add с разными результатами."""
    stats = StatsAggregator()
    
    # Успешные результаты
    success_results = [
        DeliveryResult(email=f"success{i}@example.com", success=True)
        for i in range(3)
    ]
    
    # Неуспешные результаты
    fail_results = [
        DeliveryResult(email=f"fail{i}@example.com", success=False)
        for i in range(2)
    ]
    
    # Добавляем все результаты
    for result in success_results + fail_results:
        stats.add(result)
    
    assert stats.stats['sent'] == 5
    assert stats.stats['delivered'] == 3
    assert stats.stats['failed'] == 2
    assert len(stats.events) == 5


def test_stats_with_mock_result():
    """Тестирует работу с mock объектом результата."""
    stats = StatsAggregator()
    
    # Создаем mock объект
    mock_result = Mock()
    mock_result.success = True
    mock_result.email = "mock@example.com"
    mock_result.status_code = 200
    mock_result.provider = "test"
    
    stats.add(mock_result)
    
    assert stats.stats['sent'] == 1
    assert stats.stats['delivered'] == 1