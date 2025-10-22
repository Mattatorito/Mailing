from __future__ import annotations
import os
from typing import Optional
from aiolimiter import AsyncLimiter

_limiter: Optional[AsyncLimiter] = None

def get_resend_limiter() -> AsyncLimiter:
    global _limiter
    if _limiter is None:
        # Базовый предел ~10 rps (Resend документы упоминают мягкие лимиты; можно настроить через ENV)
        rps = float(os.getenv("RESEND_RATE_RPS", "10"))
        # Ограничитель: rps токенов в секунду
        _limiter = AsyncLimiter(max(1, int(rps)), time_period=1)
    return _limiter

__all__ = ["get_resend_limiter"]
