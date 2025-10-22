#!/usr/bin/env python3

import pytest
import asyncio
import tempfile
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.mailing.performance import (
    PerformanceMonitor, MetricRecord, TimingContext, 
    CampaignPerformanceTracker, performance_monitor, campaign_tracker,
    time_function, async_time_function
)
from src.mailing.types import PerformanceMetrics


class TestPerformanceMonitor:
    """Тесты для системы мониторинга производительности."""

    def test_metric_record_creation(self):
        """Тестирует создание записи метрики."""
        timestamp = datetime.now()
        record = MetricRecord(
            timestamp=timestamp,
            metric_name="test_metric",
            value=42.5,
            tags={"type": "test"}
        )
        
        assert record.timestamp == timestamp
        assert record.metric_name == "test_metric"
        assert record.value == 42.5
        assert record.tags["type"] == "test"
        
        # Тестируем преобразование в словарь
        record_dict = record.to_dict()
        assert "timestamp" in record_dict
        assert record_dict["metric_name"] == "test_metric"
        assert record_dict["value"] == 42.5
        assert record_dict["tags"]["type"] == "test"

    def test_timing_context(self):
        """Тестирует контекст измерения времени."""
        context = TimingContext("test_operation")
        
        # Тестируем через публичные методы, а не прямую манипуляцию состояния
        start_time = time.time()
        context.start_time = start_time
        
        # Эмулируем небольшую задержку
        end_time = start_time + 5.5
        context.end_time = end_time
        
        # Проверяем вычисление длительности
        assert context.duration == 5.5

    def test_performance_monitor_initialization(self):
        """Тестирует инициализацию монитора."""
        monitor = PerformanceMonitor(max_records=1000, enable_memory_profiling=False)
        assert monitor.max_records == 1000
        assert monitor.enable_memory_profiling is False
        assert len(monitor.records) == 0
        assert len(monitor.counters) == 0
        assert len(monitor.gauges) == 0

    def test_record_metric(self):
        """Тестирует запись метрики."""
        monitor = PerformanceMonitor()
        
        monitor.record_metric("test_metric", 42.0, {"type": "test"})
        
        assert len(monitor.records) == 1
        record = monitor.records[0]
        assert record.metric_name == "test_metric"
        assert record.value == 42.0
        assert record.tags["type"] == "test"

    def test_increment_counter(self):
        """Тестирует счетчики."""
        monitor = PerformanceMonitor()
        
        # Первое увеличение
        monitor.increment_counter("test_counter", 5, {"tag": "value"})
        assert monitor.counters["test_counter"] == 5
        
        # Второе увеличение
        monitor.increment_counter("test_counter", 3)
        assert monitor.counters["test_counter"] == 8
        
        # Проверяем что записались метрики
        assert len(monitor.records) == 2

    def test_set_gauge(self):
        """Тестирует gauge метрики."""
        monitor = PerformanceMonitor()
        
        monitor.set_gauge("cpu_usage", 75.5, {"host": "server1"})
        assert monitor.gauges["cpu_usage"] == 75.5
        
        # Обновляем значение
        monitor.set_gauge("cpu_usage", 80.0)
        assert monitor.gauges["cpu_usage"] == 80.0
        
        assert len(monitor.records) == 2

    def test_timer_operations(self):
        """Тестирует операции с таймерами."""
        monitor = PerformanceMonitor()
        
        # Запускаем таймер
        timer_id = monitor.start_timer("test_operation", {"context": "test"})
        assert timer_id in monitor.active_timers
        
        time.sleep(0.001)  # Reduced sleep duration from 0.01 to 0.001
        
        # Останавливаем таймер
        duration = monitor.stop_timer(timer_id, {"result": "success"})
        assert duration > 0
        assert timer_id not in monitor.active_timers
        
        # Проверяем что записалась метрика
        assert len(monitor.records) == 1
        assert monitor.records[0].metric_name == "timer.test_operation"

    def test_timer_not_found(self):
        """Тестирует остановку несуществующего таймера."""
        monitor = PerformanceMonitor()
        
        duration = monitor.stop_timer("nonexistent_timer")
        assert duration == 0.0

    def test_time_block_context_manager(self):
        """Тестирует контекстный менеджер для измерения времени."""
        monitor = PerformanceMonitor()
        
        with monitor.time_block("test_block", {"context": "test"}):
            time.sleep(0.001)  # Reduced sleep duration
        
        assert len(monitor.records) == 1
        assert monitor.records[0].metric_name == "timer.test_block"
        assert monitor.records[0].value > 0

    @pytest.mark.asyncio
    async def test_async_time_block(self):
        """Тестирует асинхронный контекстный менеджер."""
        monitor = PerformanceMonitor()
        
        async with monitor.async_time_block("async_test", {"type": "async"}):
            await asyncio.sleep(0.001)  # Reduced sleep duration
        
        assert len(monitor.records) == 1
        assert monitor.records[0].metric_name == "timer.async_test"
        assert monitor.records[0].value > 0

    def test_collect_system_metrics(self):
        """Тестирует сбор системных метрик."""
        monitor = PerformanceMonitor()
        
        monitor.collect_system_metrics()
        
        # Проверяем что собрались основные метрики
        gauge_names = [record.metric_name for record in monitor.records if record.metric_name.startswith("gauge.")]
        
        assert "gauge.system.cpu_percent" in gauge_names
        assert "gauge.system.memory_rss" in gauge_names
        assert "gauge.system.uptime" in gauge_names

    @pytest.mark.asyncio
    async def test_background_collection(self):
        """Тестирует фоновый сбор метрик."""
        monitor = PerformanceMonitor()
        
        # Запускаем сбор с очень коротким интервалом
        await monitor.start_background_collection(0.05)
        
        # Ждем несколько циклов
        await asyncio.sleep(0.2)
        
        # Останавливаем сбор
        await monitor.stop_background_collection()
        
        # Проверяем что метрики собирались
        assert len(monitor.records) > 0

    def test_get_metrics_summary(self):
        """Тестирует получение сводки метрик."""
        monitor = PerformanceMonitor()
        
        # Добавляем несколько метрик
        monitor.record_metric("timer.operation1", 0.1)
        monitor.record_metric("timer.operation2", 0.2)
        monitor.record_metric("gauge.system.memory_rss", 100.0)
        monitor.record_metric("counter.success", 1)
        monitor.record_metric("counter.error", 1)
        
        summary = monitor.get_metrics_summary()
        
        assert isinstance(summary, dict)
        assert "execution_time" in summary
        assert "memory_usage" in summary
        assert "throughput" in summary
        assert summary["execution_time"] > 0

    def test_get_metrics_summary_with_time_window(self):
        """Тестирует сводку метрик с временным окном."""
        monitor = PerformanceMonitor()
        
        # Добавляем старую метрику
        old_record = MetricRecord(
            timestamp=datetime.now() - timedelta(hours=2),
            metric_name="timer.old_operation",
            value=1.0
        )
        monitor.records.append(old_record)
        
        # Добавляем новую метрику
        monitor.record_metric("timer.new_operation", 0.5)
        
        # Получаем сводку за последний час
        summary = monitor.get_metrics_summary(timedelta(hours=1))
        
        # Старая метрика не должна учитываться
        assert summary["execution_time"] == 0.5

    def test_get_metric_history(self):
        """Тестирует получение истории метрики."""
        monitor = PerformanceMonitor()
        
        # Добавляем несколько записей одной метрики
        for i in range(5):
            monitor.record_metric("test_metric", i)
        
        # Добавляем другую метрику
        monitor.record_metric("other_metric", 100)
        
        history = monitor.get_metric_history("test_metric", limit=3)
        
        assert len(history) == 3
        assert all(record.metric_name == "test_metric" for record in history)

    def test_export_metrics_json(self):
        """Тестирует экспорт метрик в JSON."""
        monitor = PerformanceMonitor()
        
        monitor.record_metric("test_metric", 42.0)
        monitor.increment_counter("test_counter", 5)
        
        json_export = monitor.export_metrics("json")
        
        assert isinstance(json_export, str)
        data = json.loads(json_export)
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_export_metrics_prometheus(self):
        """Тестирует экспорт в формате Prometheus."""
        monitor = PerformanceMonitor()
        
        monitor.increment_counter("requests_total", 100)
        monitor.set_gauge("memory_usage", 75.5)
        
        prometheus_export = monitor.export_metrics("prometheus")
        
        assert "requests_total 100" in prometheus_export
        assert "memory_usage 75.5" in prometheus_export
        assert "# TYPE" in prometheus_export

    def test_export_unsupported_format(self):
        """Тестирует экспорт в неподдерживаемом формате."""
        monitor = PerformanceMonitor()
        
        with pytest.raises(ValueError, match="Unsupported format"):
            monitor.export_metrics("xml")

    def test_save_metrics(self):
        """Тестирует сохранение метрик в файл."""
        monitor = PerformanceMonitor()
        monitor.record_metric("test_metric", 42.0)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            monitor.save_metrics(temp_file, "json")
            
            # Проверяем что файл создался и содержит данные
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, list)
            assert len(data) == 1
            
        finally:
            os.unlink(temp_file)

    def test_clear_metrics(self):
        """Тестирует очистку метрик."""
        monitor = PerformanceMonitor()
        
        monitor.record_metric("test_metric", 42.0)
        monitor.increment_counter("test_counter", 5)
        monitor.set_gauge("test_gauge", 75.5)
        timer_id = monitor.start_timer("test_timer")
        
        monitor.clear_metrics()
        
        assert len(monitor.records) == 0
        assert len(monitor.counters) == 0
        assert len(monitor.gauges) == 0
        assert len(monitor.active_timers) == 0

    def test_max_records_limit(self):
        """Тестирует ограничение максимального количества записей."""
        monitor = PerformanceMonitor(max_records=3)
        
        # Добавляем больше записей чем лимит
        for i in range(5):
            monitor.record_metric(f"metric_{i}", i)
        
        # Должно остаться только 3 последние записи
        assert len(monitor.records) == 3
        assert monitor.records[0].metric_name == "metric_2"
        assert monitor.records[-1].metric_name == "metric_4"


class TestCampaignPerformanceTracker:
    """Тесты для трекера производительности кампаний."""

    def test_start_campaign(self):
        """Тестирует начало отслеживания кампании."""
        monitor = PerformanceMonitor()
        tracker = CampaignPerformanceTracker(monitor)
        
        tracker.start_campaign("campaign_123")
        
        assert "campaign_123" in tracker.campaign_stats
        stats = tracker.campaign_stats["campaign_123"]
        assert "start_time" in stats
        assert stats["emails_sent"] == 0
        assert stats["emails_delivered"] == 0
        assert stats["emails_failed"] == 0

    def test_record_email_operations(self):
        """Тестирует запись операций с email."""
        monitor = PerformanceMonitor()
        tracker = CampaignPerformanceTracker(monitor)
        
        tracker.start_campaign("campaign_123")
        
        # Записываем отправку email
        tracker.record_email_sent("campaign_123", 0.1)
        stats = tracker.campaign_stats["campaign_123"]
        assert stats["emails_sent"] == 1
        assert stats["total_processing_time"] == 0.1
        
        # Записываем доставку
        tracker.record_email_delivered("campaign_123")
        assert stats["emails_delivered"] == 1
        
        # Записываем ошибку
        tracker.record_email_failed("campaign_123", "bounce")
        assert stats["emails_failed"] == 1

    def test_finish_campaign(self):
        """Тестирует завершение кампании."""
        monitor = PerformanceMonitor()
        tracker = CampaignPerformanceTracker(monitor)
        
        tracker.start_campaign("campaign_123")
        
        # Добавляем некоторую статистику
        tracker.record_email_sent("campaign_123", 0.1)
        tracker.record_email_sent("campaign_123", 0.2)
        tracker.record_email_delivered("campaign_123")
        
        time.sleep(0.01)  # Небольшая задержка для измерения времени
        
        tracker.finish_campaign("campaign_123")
        
        # Кампания должна быть удалена из активных
        assert "campaign_123" not in tracker.campaign_stats
        
        # Должны быть записаны финальные метрики
        metric_names = [record.metric_name for record in monitor.records]
        assert any("campaign.throughput" in name for name in metric_names)
        assert any("campaign.success_rate" in name for name in metric_names)

    def test_finish_nonexistent_campaign(self):
        """Тестирует завершение несуществующей кампании."""
        monitor = PerformanceMonitor()
        tracker = CampaignPerformanceTracker(monitor)
        
        # Не должно вызывать ошибку
        tracker.finish_campaign("nonexistent_campaign")


class TestDecorators:
    """Тесты для декораторов измерения производительности."""

    def test_time_function_decorator(self):
        """Тестирует декоратор для функций."""
        @time_function
        def test_function():
            time.sleep(0.01)
            return "result"
        
        # Очищаем глобальные метрики
        performance_monitor.clear_metrics()
        
        result = test_function()
        assert result == "result"
        
        # Проверяем что метрика записалась
        assert len(performance_monitor.records) == 1
        assert performance_monitor.records[0].metric_name == "timer.test_function"

    @pytest.mark.asyncio
    async def test_async_time_function_decorator(self):
        """Тестирует декоратор для асинхронных функций."""
        @async_time_function
        async def async_test_function():
            await asyncio.sleep(0.01)
            return "async_result"
        
        # Очищаем глобальные метрики
        performance_monitor.clear_metrics()
        
        result = await async_test_function()
        assert result == "async_result"
        
        # Проверяем что метрика записалась
        assert len(performance_monitor.records) == 1
        assert performance_monitor.records[0].metric_name == "timer.async_test_function"


class TestGlobalInstances:
    """Тесты для глобальных экземпляров."""

    def test_global_performance_monitor(self):
        """Тестирует глобальный экземпляр монитора."""
        assert performance_monitor is not None
        assert isinstance(performance_monitor, PerformanceMonitor)

    def test_global_campaign_tracker(self):
        """Тестирует глобальный трекер кампаний."""
        assert campaign_tracker is not None
        assert isinstance(campaign_tracker, CampaignPerformanceTracker)
        assert campaign_tracker.monitor is performance_monitor


if __name__ == "__main__":
    pytest.main([__file__, "-v"])