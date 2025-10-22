#!/usr/bin/env python3
"""
Prometheus metrics для мониторинга системы email marketing.
Собирает метрики производительности, ошибок и бизнес-логики.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from contextlib import asynccontextmanager

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary, Info,
        CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
        start_http_server, multiprocess, values
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client not installed. Metrics will be disabled.")

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Типы метрик."""
    COUNTER = "counter"
    HISTOGRAM = "histogram" 
    GAUGE = "gauge"
    SUMMARY = "summary"
    INFO = "info"

@dataclass
class MetricConfig:
    """Конфигурация метрики."""
    name: str
    description: str
    metric_type: MetricType
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # Для гистограмм

class EmailMetrics:
    """Сборщик метрик для email marketing системы."""
    
    def __init__(self, enabled: bool = True, registry: Optional[CollectorRegistry] = None):
        self.enabled = enabled and PROMETHEUS_AVAILABLE
        self.registry = registry or CollectorRegistry()
        self._metrics: Dict[str, Any] = {}
        
        if self.enabled:
            self._init_metrics()
    
    def _init_metrics(self):
        """Инициализирует метрики."""
        
        # Email delivery metrics
        self._metrics['emails_sent_total'] = Counter(
            'emails_sent_total',
            'Total number of emails sent',
            ['status', 'provider', 'template'],
            registry=self.registry
        )
        
        self._metrics['email_delivery_duration'] = Histogram(
            'email_delivery_duration_seconds',
            'Time spent delivering emails',
            ['provider', 'status'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )
        
        self._metrics['email_queue_size'] = Gauge(
            'email_queue_size',
            'Current size of email queue',
            registry=self.registry
        )
        
        # API metrics
        self._metrics['api_requests_total'] = Counter(
            'api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self._metrics['api_request_duration'] = Histogram(
            'api_request_duration_seconds',
            'Time spent processing API requests',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry
        )
        
        # Campaign metrics
        self._metrics['campaigns_total'] = Counter(
            'campaigns_total',
            'Total number of campaigns',
            ['status', 'type'],
            registry=self.registry
        )
        
        self._metrics['campaign_duration'] = Histogram(
            'campaign_duration_seconds',
            'Time spent running campaigns',
            ['status'],
            buckets=[1.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0],
            registry=self.registry
        )
        
        self._metrics['active_campaigns'] = Gauge(
            'active_campaigns',
            'Number of currently active campaigns',
            registry=self.registry
        )
        
        # Template metrics
        self._metrics['template_renders_total'] = Counter(
            'template_renders_total',
            'Total number of template renders',
            ['template', 'status'],
            registry=self.registry
        )
        
        self._metrics['template_render_duration'] = Histogram(
            'template_render_duration_seconds',
            'Time spent rendering templates',
            ['template'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
            registry=self.registry
        )
        
        # Database metrics
        self._metrics['db_operations_total'] = Counter(
            'db_operations_total',
            'Total number of database operations',
            ['operation', 'table', 'status'],
            registry=self.registry
        )
        
        self._metrics['db_operation_duration'] = Histogram(
            'db_operation_duration_seconds',
            'Time spent on database operations',
            ['operation', 'table'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
            registry=self.registry
        )
        
        self._metrics['db_connections'] = Gauge(
            'db_connections',
            'Number of active database connections',
            registry=self.registry
        )
        
        # Rate limiting metrics
        self._metrics['rate_limit_hits_total'] = Counter(
            'rate_limit_hits_total',
            'Total number of rate limit hits',
            ['limiter', 'provider'],
            registry=self.registry
        )
        
        self._metrics['rate_limit_wait_time'] = Histogram(
            'rate_limit_wait_time_seconds',
            'Time spent waiting for rate limits',
            ['limiter', 'provider'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        # System metrics
        self._metrics['memory_usage_bytes'] = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],
            registry=self.registry
        )
        
        self._metrics['cpu_usage_percent'] = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        # Error metrics
        self._metrics['errors_total'] = Counter(
            'errors_total',
            'Total number of errors',
            ['component', 'error_type'],
            registry=self.registry
        )
        
        # Business metrics
        self._metrics['recipients_processed_total'] = Counter(
            'recipients_processed_total',
            'Total number of recipients processed',
            ['status', 'source'],
            registry=self.registry
        )
        
        self._metrics['bounce_rate'] = Gauge(
            'bounce_rate',
            'Email bounce rate',
            ['provider'],
            registry=self.registry
        )
        
        self._metrics['delivery_rate'] = Gauge(
            'delivery_rate',
            'Email delivery rate',
            ['provider'],
            registry=self.registry
        )
        
        # Application info
        self._metrics['app_info'] = Info(
            'app_info',
            'Application information',
            registry=self.registry
        )
        
        # Set application info
        self._metrics['app_info'].info({
            'version': '1.0.0',
            'python_version': '3.11',
            'environment': 'production'
        })
    
    def record_email_sent(self, status: str, provider: str = "resend", template: str = "unknown"):
        """Записывает отправку email."""
        if self.enabled:
            self._metrics['emails_sent_total'].labels(
                status=status, 
                provider=provider, 
                template=template
            ).inc()
    
    @asynccontextmanager
    async def time_email_delivery(self, provider: str = "resend", status: str = "success"):
        """Контекстный менеджер для измерения времени доставки."""
        if not self.enabled:
            yield
            return
            
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self._metrics['email_delivery_duration'].labels(
                provider=provider,
                status=status
            ).observe(duration)
    
    def set_queue_size(self, size: int):
        """Устанавливает размер очереди email."""
        if self.enabled:
            self._metrics['email_queue_size'].set(size)
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Записывает API запрос."""
        if self.enabled:
            self._metrics['api_requests_total'].labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            
            self._metrics['api_request_duration'].labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    def record_campaign(self, status: str, campaign_type: str = "email"):
        """Записывает кампанию."""
        if self.enabled:
            self._metrics['campaigns_total'].labels(
                status=status,
                type=campaign_type
            ).inc()
    
    @asynccontextmanager
    async def time_campaign(self, status: str = "completed"):
        """Контекстный менеджер для измерения времени кампании."""
        if not self.enabled:
            yield
            return
            
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self._metrics['campaign_duration'].labels(status=status).observe(duration)
    
    def set_active_campaigns(self, count: int):
        """Устанавливает количество активных кампаний."""
        if self.enabled:
            self._metrics['active_campaigns'].set(count)
    
    def record_template_render(self, template: str, status: str = "success"):
        """Записывает рендеринг шаблона."""
        if self.enabled:
            self._metrics['template_renders_total'].labels(
                template=template,
                status=status
            ).inc()
    
    @asynccontextmanager
    async def time_template_render(self, template: str):
        """Контекстный менеджер для измерения времени рендеринга."""
        if not self.enabled:
            yield
            return
            
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self._metrics['template_render_duration'].labels(template=template).observe(duration)
    
    def record_db_operation(self, operation: str, table: str, status: str = "success"):
        """Записывает операцию с БД."""
        if self.enabled:
            self._metrics['db_operations_total'].labels(
                operation=operation,
                table=table,
                status=status
            ).inc()
    
    @asynccontextmanager
    async def time_db_operation(self, operation: str, table: str):
        """Контекстный менеджер для измерения времени БД операций."""
        if not self.enabled:
            yield
            return
            
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self._metrics['db_operation_duration'].labels(
                operation=operation,
                table=table
            ).observe(duration)
    
    def set_db_connections(self, count: int):
        """Устанавливает количество подключений к БД."""
        if self.enabled:
            self._metrics['db_connections'].set(count)
    
    def record_rate_limit_hit(self, limiter: str, provider: str = "resend"):
        """Записывает попадание в rate limit."""
        if self.enabled:
            self._metrics['rate_limit_hits_total'].labels(
                limiter=limiter,
                provider=provider
            ).inc()
    
    @asynccontextmanager
    async def time_rate_limit_wait(self, limiter: str, provider: str = "resend"):
        """Контекстный менеджер для измерения времени ожидания rate limit."""
        if not self.enabled:
            yield
            return
            
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if duration > 0.01:  # Записываем только значимые ожидания
                self._metrics['rate_limit_wait_time'].labels(
                    limiter=limiter,
                    provider=provider
                ).observe(duration)
    
    def set_memory_usage(self, usage_bytes: int, memory_type: str = "rss"):
        """Устанавливает использование памяти."""
        if self.enabled:
            self._metrics['memory_usage_bytes'].labels(type=memory_type).set(usage_bytes)
    
    def set_cpu_usage(self, usage_percent: float):
        """Устанавливает использование CPU."""
        if self.enabled:
            self._metrics['cpu_usage_percent'].set(usage_percent)
    
    def record_error(self, component: str, error_type: str):
        """Записывает ошибку."""
        if self.enabled:
            self._metrics['errors_total'].labels(
                component=component,
                error_type=error_type
            ).inc()
    
    def record_recipient_processed(self, status: str, source: str = "csv"):
        """Записывает обработку получателя."""
        if self.enabled:
            self._metrics['recipients_processed_total'].labels(
                status=status,
                source=source
            ).inc()
    
    def set_bounce_rate(self, rate: float, provider: str = "resend"):
        """Устанавливает bounce rate."""
        if self.enabled:
            self._metrics['bounce_rate'].labels(provider=provider).set(rate)
    
    def set_delivery_rate(self, rate: float, provider: str = "resend"):
        """Устанавливает delivery rate."""
        if self.enabled:
            self._metrics['delivery_rate'].labels(provider=provider).set(rate)
    
    def get_metrics(self) -> str:
        """Возвращает метрики в формате Prometheus."""
        if not self.enabled:
            return ""
        
        return generate_latest(self.registry).decode('utf-8')
    
    def get_content_type(self) -> str:
        """Возвращает content type для метрик."""
        return CONTENT_TYPE_LATEST

class SystemMetricsCollector:
    """Сборщик системных метрик."""
    
    def __init__(self, metrics: EmailMetrics):
        self.metrics = metrics
        self._running = False
        self._task = None
    
    async def start(self):
        """Запускает сбор системных метрик."""
        if self._running or not self.metrics.enabled:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._collect_loop())
        logger.info("System metrics collector started")
    
    async def stop(self):
        """Останавливает сбор метрик."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("System metrics collector stopped")
    
    async def _collect_loop(self):
        """Основной цикл сбора метрик."""
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not available, system metrics disabled")
            return
        
        while self._running:
            try:
                # Память
                memory = psutil.virtual_memory()
                self.metrics.set_memory_usage(memory.used, "used")
                self.metrics.set_memory_usage(memory.available, "available")
                
                # CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics.set_cpu_usage(cpu_percent)
                
                # Процесс
                process = psutil.Process()
                process_memory = process.memory_info()
                self.metrics.set_memory_usage(process_memory.rss, "process_rss")
                self.metrics.set_memory_usage(process_memory.vms, "process_vms")
                
                await asyncio.sleep(30)  # Собираем каждые 30 секунд
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(60)  # Ждем минуту при ошибке

# Глобальный экземпляр
metrics: Optional[EmailMetrics] = None
system_collector: Optional[SystemMetricsCollector] = None

def get_metrics() -> EmailMetrics:
    """Получает экземпляр сборщика метрик."""
    global metrics
    if not metrics:
        import os
        enabled = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
        metrics = EmailMetrics(enabled=enabled)
    return metrics

async def start_metrics_collection():
    """Запускает сбор метрик."""
    global system_collector
    
    metrics_instance = get_metrics()
    if not metrics_instance.enabled:
        return
    
    system_collector = SystemMetricsCollector(metrics_instance)
    await system_collector.start()

async def stop_metrics_collection():
    """Останавливает сбор метрик."""
    if system_collector:
        await system_collector.stop()

def start_metrics_server(port: int = 8000):
    """Запускает HTTP сервер для метрик."""
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus client not available, metrics server not started")
        return
    
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")

# Декораторы для автоматического сбора метрик
def track_api_request(endpoint: str):
    """Декоратор для отслеживания API запросов."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            method = "unknown"
            status_code = 200
            
            try:
                # Пытаемся извлечь метод из request
                if args and hasattr(args[0], 'method'):
                    method = args[0].method
                
                result = await func(*args, **kwargs)
                
                # Пытаемся извлечь status code из response
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                
                return result
                
            except Exception as e:
                status_code = 500
                get_metrics().record_error("api", type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                get_metrics().record_api_request(method, endpoint, status_code, duration)
        
        return wrapper
    return decorator

def track_template_render(template_name: str):
    """Декоратор для отслеживания рендеринга шаблонов."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                async with get_metrics().time_template_render(template_name):
                    result = await func(*args, **kwargs)
                
                get_metrics().record_template_render(template_name, "success")
                return result
                
            except Exception as e:
                get_metrics().record_template_render(template_name, "error")
                get_metrics().record_error("templating", type(e).__name__)
                raise
        
        return wrapper
    return decorator