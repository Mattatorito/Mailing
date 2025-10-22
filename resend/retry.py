from __future__ import annotations
import asyncio, random
from typing import Callable, Awaitable, TypeVar, Optional
from mailing.logging_config import retry_logger

T = TypeVar('T')

def _compute_delay(exc: Exception, attempt: int, base_delay: float) -> float:
    """Экспоненциальный backoff с джиттером и особыми случаями (429/5xx, Retry-After)."""
    effective_base = base_delay
    status_code = getattr(exc, 'status_code', None)
    if status_code == 429:
        effective_base = 0.6
    elif isinstance(status_code, int) and 500 <= status_code <= 599:
        effective_base = 1.2
    jitter = 0.5 + random.random()  # [0.5, 1.5)
    delay = effective_base * (2 ** attempt) * jitter
    retry_after = getattr(exc, 'retry_after', None)
    if isinstance(retry_after, (int, float)) and retry_after > 0:
        delay = max(delay, float(retry_after))
    return min(delay, 60.0)

async def with_retry(fn: Callable[[], Awaitable[T]], *, retries: int, base_delay: float = 1.0) -> T:
    """Универсальный retry с экспоненциальным бэкоффом.

    Останавливается немедленно, если исключение имеет retriable=False.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            return await fn()
        except Exception as e:  # noqa
            if getattr(e, 'retriable', True) is False:
                raise
            last_exc = e
            if attempt == retries:
                break
            delay = _compute_delay(e, attempt, base_delay)
            try:
                retry_logger.warning(
                    "retry attempt=%s status=%s delay=%.2fs retry_after=%s retriable=%s",
                    attempt + 1, getattr(e, 'status_code', None), delay, getattr(e, 'retry_after', None), getattr(e, 'retriable', True)
                )
            except Exception:  # noqa
                pass
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc

__all__ = ["with_retry", "_compute_delay"]
