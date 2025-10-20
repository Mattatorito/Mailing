from __future__ import annotations
from typing import Optional, Dict
import asyncio
import os

from aiolimiter import AsyncLimiter

from mailing.config import settings

# Словарь лимитеров по event loop для избежания предупреждений aiolimiter
_limiters: Dict[asyncio.AbstractEventLoop, AsyncLimiter] = {}


def get_resend_limiter() -> AsyncLimiter:
    """Получить rate limiter для текущего event loop.

    Создает новый лимитер для каждого event loop во избежание
    предупреждений о переиспользовании AsyncLimiter между loops."""
    loop = asyncio.get_event_loop()

    if loop not in _limiters:
        # Преобразуем минутный лимит в RPS, чтобы согласовать с настройками приложения
        per_minute = max(
            1,
            int(os.getenv("RATE_LIMIT_PER_MINUTE", str(settings.rate_limit_per_minute))
            ),
        )
        rps = max(1, per_minute // 60)  # целочисленно, чтобы не превышать
        _limiters[loop] = AsyncLimiter(rps, time_period = 1)

    return _limiters[loop]

__all__ = ["get_resend_limiter"]
