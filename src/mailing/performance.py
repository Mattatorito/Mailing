#!/usr/bin/env python3
"""
Система мониторинга производительности для email marketing tool.
Измеряет время выполнения, использование памяти, throughput и другие метрики.
"""

from __future__ import annotations
import time
import psutil
import asyncio
import threading
import uuid
from contextlib import contextmanager, asynccontextmanager
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from collections import deque
import json
from pathlib import Path

from src.mailing.types import PerformanceMetrics
from src.mailing.logging_config import logger


def get_utc_now() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)
from src.mailing.logging_config import logger


@dataclass
class MetricRecord:
    """Запись метрики производительности."""
    timestamp: datetime
    metric_name: str
    value: Union[float, int]
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует запись в словарь."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'metric_name': self.metric_name,
            'value': self.value,
            'tags': self.tags
        }


@dataclass
class TimingContext:
    """Контекст для измерения времени выполнения."""
    name: str
    start_time: float = 0.0
    end_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Возвращает длительность в секундах."""
        return self.end_time - self.start_time if self.end_time > 0 else 0.0


class PerformanceMonitor:
    """Монитор производительности с поддержкой различных метрик."""
    
    def __init__(self, max_records: int = 10000, enable_memory_profiling: bool = True):
        """Инициализирует монитор производительности."""
        self.max_records = max_records
        self.enable_memory_profiling = enable_memory_profiling
        self.records: deque[MetricRecord] = deque(maxlen=max_records)
        self.active_timers: Dict[str, TimingContext] = {}
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()
        
        # Системные метрики
        self.process = psutil.Process()
        self._collect_system_metrics_task: Optional[asyncio.Task] = None
        
    async def start_background_collection(self, interval: float = 30.0):
        """Запускает фоновый сбор системных метрик."""
        self._collect_system_metrics_task = asyncio.create_task(
            self._background_system_metrics(interval)
        )
        
    async def stop_background_collection(self):
        """Останавливает фоновый сбор метрик."""
        if self._collect_system_metrics_task:
            self._collect_system_metrics_task.cancel()
            try:
                await self._collect_system_metrics_task
            except asyncio.CancelledError:
                pass
            finally:
                self._collect_system_metrics_task = None
                
    def cleanup_stale_timers(self, max_age_seconds: float = 3600):
        """Очищает застрявшие таймеры старше указанного времени."""
        current_time = time.time()
        stale_timers = []
        
        with self._lock:
            for timer_id, timer in self.active_timers.items():
                if current_time - timer.start_time > max_age_seconds:
                    stale_timers.append(timer_id)
            
            for timer_id in stale_timers:
                timer = self.active_timers.pop(timer_id, None)
                if timer:
                    logger.warning(f"Cleaned up stale timer: {timer.name} (age: {current_time - timer.start_time:.1f}s)")
        
        return len(stale_timers)
    
    async def _background_system_metrics(self, interval: float):
        """Фоновая задача для сбора системных метрик."""
        cleanup_counter = 0
        while True:
            try:
                self.collect_system_metrics()
                
                # Очищаем застрявшие таймеры каждые 10 циклов
                cleanup_counter += 1
                if cleanup_counter >= 10:
                    self.cleanup_stale_timers()
                    cleanup_counter = 0
                
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(interval)
    
    def record_metric(self, name: str, value: Union[float, int], tags: Optional[Dict[str, str]] = None):
        """Записывает метрику."""
        with self._lock:
            record = MetricRecord(
                timestamp=get_utc_now(),
                metric_name=name,
                value=value,
                tags=tags or {}
            )
            self.records.append(record)
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Увеличивает счетчик."""
        with self._lock:
            self.counters[name] = self.counters.get(name, 0) + value
        self.record_metric(f"counter.{name}", self.counters[name], tags)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Устанавливает значение gauge метрики."""
        with self._lock:
            self.gauges[name] = value
        self.record_metric(f"gauge.{name}", value, tags)
    
    def start_timer(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Запускает таймер и возвращает его ID."""
        timer_id = f"{name}_{time.time()}"
        timer = TimingContext(
            name=name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self.active_timers[timer_id] = timer
        
        return timer_id
    
    def stop_timer(self, timer_id: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Останавливает таймер и записывает метрику."""
        with self._lock:
            timer = self.active_timers.pop(timer_id, None)
        
        if timer is None:
            logger.warning(f"Timer {timer_id} not found")
            return 0.0
        
        timer.end_time = time.time()
        duration = timer.duration
        
        # Записываем метрику времени
        self.record_metric(f"timer.{timer.name}", duration, tags)
        
        return duration
    
    @contextmanager
    def time_block(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Контекстный менеджер для измерения времени выполнения блока кода."""
        timer_id = self.start_timer(name)
        try:
            yield
        finally:
            self.stop_timer(timer_id, tags)
    
    @asynccontextmanager
    async def async_time_block(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Асинхронный контекстный менеджер для измерения времени."""
        timer_id = self.start_timer(name)
        try:
            yield
        finally:
            self.stop_timer(timer_id, tags)
    
    def collect_system_metrics(self):
        """Собирает системные метрики."""
        try:
            # CPU и память
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            self.set_gauge("system.cpu_percent", cpu_percent)
            self.set_gauge("system.memory_rss", memory_info.rss / 1024 / 1024)  # MB
            self.set_gauge("system.memory_vms", memory_info.vms / 1024 / 1024)  # MB
            self.set_gauge("system.memory_percent", memory_percent)
            
            # Количество потоков
            num_threads = self.process.num_threads()
            self.set_gauge("system.threads", num_threads)
            
            # Файловые дескрипторы (только на Unix)
            try:
                num_fds = self.process.num_fds()
                self.set_gauge("system.file_descriptors", num_fds)
            except AttributeError:
                pass  # Windows не поддерживает num_fds
            
            # Время работы приложения
            uptime = time.time() - self._start_time
            self.set_gauge("system.uptime", uptime)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def get_metrics_summary(self, time_window: Optional[timedelta] = None) -> PerformanceMetrics:
        """Возвращает сводку метрик за указанный период."""
        now = get_utc_now()
        cutoff_time = now - time_window if time_window else None
        
        # Фильтруем записи по времени
        filtered_records = [
            record for record in self.records
            if cutoff_time is None or record.timestamp >= cutoff_time
        ]
        
        if not filtered_records:
            return PerformanceMetrics(
                execution_time=0.0,
                memory_usage=0.0,
                throughput=0.0,
                errors_per_minute=0.0,
                success_rate=0.0
            )
        
        # Вычисляем метрики
        timer_records = [r for r in filtered_records if r.metric_name.startswith('timer.')]
        memory_records = [r for r in filtered_records if 'memory' in r.metric_name]
        error_records = [r for r in filtered_records if 'error' in r.metric_name]
        success_records = [r for r in filtered_records if 'success' in r.metric_name]
        
        # Среднее время выполнения
        avg_execution_time = (
            sum(r.value for r in timer_records) / len(timer_records)
            if timer_records else 0.0
        )
        
        # Среднее использование памяти
        avg_memory_usage = (
            sum(r.value for r in memory_records) / len(memory_records)
            if memory_records else 0.0
        )
        
        # Throughput (запросов в секунду)
        if filtered_records:
            time_span = (filtered_records[-1].timestamp - filtered_records[0].timestamp).total_seconds()
            throughput = len(filtered_records) / max(time_span, 1.0)
        else:
            throughput = 0.0
        
        # Ошибки в минуту
        if time_window:
            minutes = time_window.total_seconds() / 60
            errors_per_minute = len(error_records) / max(minutes, 1.0)
        else:
            errors_per_minute = 0.0
        
        # Процент успеха
        total_operations = len(success_records) + len(error_records)
        success_rate = (
            len(success_records) / total_operations
            if total_operations > 0 else 1.0
        )
        
        return PerformanceMetrics(
            execution_time=avg_execution_time,
            memory_usage=avg_memory_usage,
            throughput=throughput,
            errors_per_minute=errors_per_minute,
            success_rate=success_rate
        )
    
    def get_metric_history(self, metric_name: str, limit: int = 100) -> List[MetricRecord]:
        """Возвращает историю определенной метрики."""
        matching_records = [
            record for record in self.records
            if record.metric_name == metric_name
        ]
        return matching_records[-limit:] if matching_records else []
    
    def export_metrics(self, format: str = 'json') -> str:
        """Экспортирует метрики в указанном формате."""
        if format == 'json':
            return json.dumps([record.to_dict() for record in self.records], indent=2)
        elif format == 'prometheus':
            return self._export_prometheus()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_prometheus(self) -> str:
        """Экспортирует метрики в формате Prometheus."""
        lines = []
        
        # Счетчики
        for name, value in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # Gauge метрики
        for name, value in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        return '\n'.join(lines)
    
    def save_metrics(self, filepath: Union[str, Path], format: str = 'json', backup: bool = True):
        """Сохраняет метрики в файл с возможностью создания резервной копии."""
        filepath = Path(filepath)
        content = self.export_metrics(format)
        
        # Создаем резервную копию существующего файла если нужно
        if backup and filepath.exists():
            # Используем UUID для уникальности имен резервных копий
            backup_suffix = f'.backup_{int(time.time())}_{uuid.uuid4().hex[:8]}{filepath.suffix}'
            backup_path = filepath.with_suffix(backup_suffix)
            try:
                import shutil
                shutil.copy2(filepath, backup_path)
                logger.info(f"Backup created: {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Сохраняем файл атомарно через временный файл с уникальным именем
        temp_suffix = f'.tmp_{int(time.time())}_{uuid.uuid4().hex[:8]}{filepath.suffix}'
        temp_filepath = filepath.with_suffix(temp_suffix)
        try:
            with open(temp_filepath, 'w') as f:
                f.write(content)
            
            # Атомарно перемещаем временный файл на место целевого
            temp_filepath.replace(filepath)
            logger.info(f"Metrics saved to {filepath}")
            
        except Exception as e:
            # Удаляем временный файл при ошибке
            if temp_filepath.exists():
                temp_filepath.unlink()
            raise e
    
    def clear_metrics(self):
        """Очищает все собранные метрики."""
        with self._lock:
            self.records.clear()
            self.counters.clear()
            self.gauges.clear()
            self.active_timers.clear()
            
    async def shutdown(self):
        """Корректно закрывает монитор и очищает ресурсы."""
        # Останавливаем фоновые задачи
        await self.stop_background_collection()
        
        # Очищаем все активные таймеры
        with self._lock:
            stale_count = len(self.active_timers)
            if stale_count > 0:
                logger.warning(f"Shutting down with {stale_count} active timers")
            self.active_timers.clear()
        
        logger.info("PerformanceMonitor shutdown complete")


# Глобальный экземпляр монитора
performance_monitor = PerformanceMonitor()


def time_function(func: Callable) -> Callable:
    """Декоратор для измерения времени выполнения функции."""
    def wrapper(*args, **kwargs):
        with performance_monitor.time_block(func.__name__):
            return func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def async_time_function(func: Callable) -> Callable:
    """Декоратор для измерения времени выполнения асинхронной функции."""
    async def wrapper(*args, **kwargs):
        async with performance_monitor.async_time_block(func.__name__):
            return await func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# Campaign performance monitoring
class CampaignPerformanceTracker:
    """Специализированный трекер для мониторинга производительности кампаний."""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.campaign_stats: Dict[str, Dict[str, Any]] = {}
        self._stats_lock = threading.Lock()  # Use Lock instead of RLock for better performance
    
    def start_campaign(self, campaign_id: str):
        """Начинает отслеживание кампании."""
        with self._stats_lock:
            self.campaign_stats[campaign_id] = {
                'start_time': time.time(),
                'emails_sent': 0,
                'emails_delivered': 0,
                'emails_failed': 0,
                'total_processing_time': 0.0
            }
        
        self.monitor.increment_counter('campaigns.started')
    
    def record_email_sent(self, campaign_id: str, processing_time: float):
        """Записывает отправку email."""
        with self._stats_lock:
            if campaign_id in self.campaign_stats:
                stats = self.campaign_stats[campaign_id]
                stats['emails_sent'] += 1
                stats['total_processing_time'] += processing_time
        
        self.monitor.increment_counter('emails.sent')
        self.monitor.record_metric('email.processing_time', processing_time)
    
    def record_email_delivered(self, campaign_id: str):
        """Записывает доставку email."""
        with self._stats_lock:
            if campaign_id in self.campaign_stats:
                self.campaign_stats[campaign_id]['emails_delivered'] += 1
        
        self.monitor.increment_counter('emails.delivered')
    
    def record_email_failed(self, campaign_id: str, error_type: str):
        """Записывает ошибку отправки email."""
        with self._stats_lock:
            if campaign_id in self.campaign_stats:
                self.campaign_stats[campaign_id]['emails_failed'] += 1
        
        self.monitor.increment_counter('emails.failed')
        self.monitor.increment_counter(f'emails.failed.{error_type}')
    
    def finish_campaign(self, campaign_id: str):
        """Завершает отслеживание кампании."""
        with self._stats_lock:
            if campaign_id not in self.campaign_stats:
                return
            
            stats = self.campaign_stats[campaign_id].copy()  # Копируем для безопасности
            # Удаляем статистику кампании сразу
            del self.campaign_stats[campaign_id]
        
        # Вычисляем метрики кампании (вне блокировки)
        end_time = time.time()
        total_time = end_time - stats['start_time']
        
        emails_sent = stats['emails_sent']
        emails_delivered = stats['emails_delivered']
        emails_failed = stats['emails_failed']
        
        # Throughput
        if total_time > 0:
            throughput = emails_sent / total_time
            self.monitor.record_metric('campaign.throughput', throughput)
        
        # Success rate
        if emails_sent > 0:
            success_rate = emails_delivered / emails_sent
            self.monitor.record_metric('campaign.success_rate', success_rate)
        
        # Average processing time
        if emails_sent > 0:
            avg_processing_time = stats['total_processing_time'] / emails_sent
            self.monitor.record_metric('campaign.avg_processing_time', avg_processing_time)
        
        self.monitor.record_metric('campaign.duration', total_time)
        self.monitor.record_metric('campaign.emails_sent', emails_sent)
        self.monitor.increment_counter('campaigns.completed')


# Глобальный трекер кампаний
campaign_tracker = CampaignPerformanceTracker(performance_monitor)