#!/usr/bin/env python3

from __future__ import annotations
import asyncio
import time
from typing import Dict, Optional
from collections import deque


class RateLimiter:
    """Ограничитель скорости для API запросов."""
    
    def __init__(
        self,
        max_requests: int,
        time_window: float,
        burst_limit: Optional[int] = None
    ):
        """Инициализирует ограничитель скорости.
        
        Args:
            max_requests: Максимальное количество запросов
            time_window: Временное окно в секундах
            burst_limit: Максимальное количество запросов в "пачке"
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_limit = burst_limit or max_requests
        
        self.requests: deque = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Получает разрешение на выполнение запроса."""
        async with self._lock:
            now = time.time()
            
            # Удаляем старые запросы
            while self.requests and now - self.requests[0] > self.time_window:
                self.requests.popleft()
            
            # Проверяем лимиты
            if len(self.requests) >= self.max_requests:
                return False
            
            # Добавляем текущий запрос
            self.requests.append(now)
            return True
    
    async def wait_for_slot(self) -> None:
        """Ждет освобождения слота для запроса."""
        while not await self.acquire():
            # Вычисляем время ожидания
            if self.requests:
                oldest_request = self.requests[0]
                wait_time = self.time_window - (time.time() - oldest_request)
                if wait_time > 0:
                    await asyncio.sleep(min(wait_time, 1.0))
                else:
                    await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.1)
    
    def get_remaining_requests(self) -> int:
        """Возвращает количество оставшихся запросов."""
        now = time.time()
        
        # Удаляем старые запросы
        while self.requests and now - self.requests[0] > self.time_window:
            self.requests.popleft()
        
        return max(0, self.max_requests - len(self.requests))
    
    def get_reset_time(self) -> float:
        """Возвращает время до сброса лимита."""
        if not self.requests:
            return 0.0
        
        oldest_request = self.requests[0]
        return max(0.0, self.time_window - (time.time() - oldest_request))


# Глобальные лимитеры для разных сервисов
_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(
    name: str,
    max_requests: int,
    time_window: float,
    burst_limit: Optional[int] = None
) -> RateLimiter:
    """Получает или создает ограничитель скорости."""
    loop = asyncio.get_event_loop()
    
    if loop not in _limiters:
        _limiters[loop] = {}
    
    if name not in _limiters[loop]:
        _limiters[loop][name] = RateLimiter(
            max_requests=max_requests,
            time_window=time_window,
            burst_limit=burst_limit
        )
    
    return _limiters[loop][name]


# Предустановленные лимитеры для популярных сервисов
def get_resend_limiter() -> RateLimiter:
    """Получает лимитер для Resend API."""
    # Resend: 10 запросов в секунду
    return get_rate_limiter("resend", max_requests=10, time_window=1.0)


def get_mailgun_limiter() -> RateLimiter:
    """Получает лимитер для Mailgun API."""
    # Mailgun: 100 запросов в секунду
    return get_rate_limiter("mailgun", max_requests=100, time_window=1.0)


def get_sendgrid_limiter() -> RateLimiter:
    """Получает лимитер для SendGrid API."""
    # SendGrid: 600 запросов в минуту
    return get_rate_limiter("sendgrid", max_requests=600, time_window=60.0)


class RateLimitedClient:
    """Базовый клиент с поддержкой ограничения скорости."""
    
    def __init__(self, rate_limiter: RateLimiter):
        """Инициализирует клиент с ограничителем скорости."""
        self.rate_limiter = rate_limiter
    
    async def make_request(self, request_func, *args, **kwargs):
        """Выполняет запрос с учетом ограничений скорости."""
        await self.rate_limiter.wait_for_slot()
        
        try:
            return await request_func(*args, **kwargs)
        except Exception as e:
            # Если это ошибка rate limiting от сервера,
            # ждем дополнительное время
            if hasattr(e, 'status_code') and e.status_code == 429:
                await asyncio.sleep(5.0)
            raise


async def with_rate_limit(
    rate_limiter: RateLimiter,
    func,
    *args,
    **kwargs
):
    """Выполняет функцию с ограничением скорости."""
    await rate_limiter.wait_for_slot()
    return await func(*args, **kwargs)


def rate_limited(
    max_requests: int,
    time_window: float,
    name: Optional[str] = None
):
    """Декоратор для ограничения скорости функций."""
    def decorator(func):
        limiter_name = name or f"{func.__module__}.{func.__name__}"
        
        async def wrapper(*args, **kwargs):
            limiter = get_rate_limiter(limiter_name, max_requests, time_window)
            return await with_rate_limit(limiter, func, *args, **kwargs)
        
        return wrapper
    return decorator
