#!/usr/bin/env python3
"""
Дополнительные типы для системы массовой рассылки.
Центральное место для всех type hints проекта.
"""

from __future__ import annotations
from typing import (
    TYPE_CHECKING, 
    TypedDict, 
    Protocol, 
    Union, 
    Any, 
    Dict, 
    List, 
    Optional,
    Awaitable,
    AsyncIterator,
    Callable
)
from datetime import datetime
from pathlib import Path

if TYPE_CHECKING:
    from src.mailing.models import Recipient, DeliveryResult
    from aiohttp.web import Request, Response


# Event types для системы событий
class EventData(TypedDict, total=False):
    """Структура данных события."""
    type: str
    email: str
    timestamp: str
    message_id: str
    error: str
    provider: str
    status_code: int


class StatsData(TypedDict):
    """Структура статистических данных."""
    sent: int
    delivered: int
    failed: int
    bounced: int
    opened: int
    clicked: int
    unsubscribed: int
    success_rate: float
    total_events: int
    last_updated: str


class WebhookPayload(TypedDict, total=False):
    """Структура webhook payload."""
    type: str
    data: Dict[str, Any]
    created_at: str


class PreflightResult(TypedDict, total=False):
    """Результат предварительных проверок."""
    environment: Dict[str, Any]
    template: Dict[str, Any]
    recipients: Dict[str, Any]
    status: str
    errors: List[str]
    warnings: List[str]


# Protocol для загрузчиков данных
class DataLoader(Protocol):
    """Протокол для загрузчиков данных."""
    
    def validate_source(self, source: str) -> bool:
        """Проверяет валидность источника данных."""
        ...
    
    def load(self, source: str) -> List[Recipient]:
        """Загружает данные из источника."""
        ...


# Protocol для репозиториев
class Repository(Protocol):
    """Базовый протокол для репозиториев."""
    
    def save(self, data: Any) -> None:
        """Сохраняет данные."""
        ...


# Типы для конфигурации
ConfigValue = Union[str, int, float, bool, None]
ConfigDict = Dict[str, ConfigValue]

# Типы для шаблонизации
TemplateContext = Dict[str, Any]
TemplateResult = str

# Типы для валидации
ValidationResult = Dict[str, Union[bool, str, List[str]]]

# Типы для CLI
CliArgument = Union[str, int, float, bool]
CliArguments = Dict[str, CliArgument]

# Типы для webhook сервера
if TYPE_CHECKING:
    WebhookHandler = Callable[[Request], Awaitable[Response]]
else:
    WebhookHandler = Callable

# Типы для кампаний
CampaignEvent = Dict[str, Any]
CampaignIterator = AsyncIterator[CampaignEvent]

# Типы для метрик производительности
class PerformanceMetrics(TypedDict):
    """Метрики производительности."""
    execution_time: float
    memory_usage: float
    throughput: float
    errors_per_minute: float
    success_rate: float


# Типы для лимитов
class QuotaInfo(TypedDict):
    """Информация о квотах."""
    daily_limit: int
    current_usage: int
    remaining: int
    reset_time: str


# Callback типы
ProgressCallback = Callable[[int, int], None]
ErrorCallback = Callable[[str, Exception], None]
CompletionCallback = Callable[[StatsData], None]

# Типы файловых путей
FilePath = Union[str, Path]