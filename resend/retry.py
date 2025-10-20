#!/usr/bin/env python3

from __future__ import annotations
import asyncio
import random
from typing import Callable, Any, TypeVar, Awaitable
from functools import wraps

T = TypeVar('T')


async def retry_with_backoff(
    func: Callable[..., Awaitable[T]],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    **kwargs
) -> T:
    """Выполняет функцию с повторными попытками при ошибках.
    
    Args:
        func: Асинхронная функция для выполнения
        max_retries: Максимальное количество попыток
        base_delay: Базовая задержка в секундах
        max_delay: Максимальная задержка в секундах
        backoff_factor: Множитель для экспоненциального backoff
        jitter: Добавлять ли случайный jitter к задержке
    
    Returns:
        Результат выполнения функции
    
    Raises:
        Exception: Последняя пойманная ошибка если все попытки исчерпаны
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt == max_retries:
                # Последняя попытка - пробрасываем ошибку
                raise e
            
            # Вычисляем задержку
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            
            # Добавляем jitter если нужно
            if jitter:
                delay *= (0.5 + random.random() * 0.5)
            
            await asyncio.sleep(delay)
    
    # Это никогда не должно выполниться, но на всякий случай
    if last_exception:
        raise last_exception


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True
):
    """Декоратор для автоматических повторных попыток.
    
    Args:
        max_retries: Максимальное количество попыток
        base_delay: Базовая задержка в секундах
        max_delay: Максимальная задержка в секундах
        backoff_factor: Множитель для экспоненциального backoff
        jitter: Добавлять ли случайный jitter к задержке
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
                jitter=jitter,
                **kwargs
            )
        return wrapper
    return decorator


class RetryableError(Exception):
    """Базовый класс для ошибок, которые можно повторить."""
    pass


class NonRetryableError(Exception):
    """Базовый класс для ошибок, которые нельзя повторить."""
    pass


def is_retryable_error(error: Exception) -> bool:
    """Определяет, можно ли повторить операцию при данной ошибке."""
    
    # Определенно повторяемые ошибки
    if isinstance(error, RetryableError):
        return True
    
    # Определенно не повторяемые ошибки
    if isinstance(error, NonRetryableError):
        return False
    
    # HTTP ошибки
    if hasattr(error, 'status') or hasattr(error, 'status_code'):
        status = getattr(error, 'status', None) or getattr(error, 'status_code', None)
        if status:
            # Повторяем для временных ошибок сервера
            return status >= 500 or status == 429  # Server errors or rate limiting
    
    # Сетевые ошибки
    import aiohttp
    if isinstance(error, (aiohttp.ClientError, asyncio.TimeoutError)):
        return True
    
    # По умолчанию не повторяем
    return False


async def smart_retry(
    func: Callable[..., Awaitable[T]],
    *args,
    max_retries: int = 3,
    **kwargs
) -> T:
    """Умные повторные попытки с анализом типа ошибки."""
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries or not is_retryable_error(e):
                raise e
            
            # Задержка зависит от типа ошибки
            if hasattr(e, 'status_code') and e.status_code == 429:
                # Rate limiting - ждем дольше
                delay = 30.0 * (attempt + 1)
            else:
                # Обычная экспоненциальная задержка
                delay = min(2.0 ** attempt, 30.0)
            
            await asyncio.sleep(delay)
    
    raise RuntimeError("This should never be reached")
