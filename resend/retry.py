from __future__ import annotations
import asyncio
from typing import TypeVar, Callable, Awaitable
from mailing.logging_config import logger

T = TypeVar('T')


async def with_retry(
    func: Callable[[], Awaitable[T]], 
    retries: int = 3, 
    delay: float = 1.0
) -> T:
    """Выполняет функцию с повторными попытками при ошибках.
    
    Args:
        func: Асинхронная функция для выполнения
        retries: Количество попыток
        delay: Задержка между попытками в секундах
        
    Returns:
        Результат выполнения функции
        
    Raises:
        Exception: Последняя ошибка если все попытки неудачны
    """
    last_exception = None
    
    for attempt in range(retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            if attempt < retries:
                logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(f"All {retries + 1} attempts failed, giving up")
    
    # Если мы дошли сюда, все попытки провалились
    raise last_exception