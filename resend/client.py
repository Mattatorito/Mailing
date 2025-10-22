from __future__ import annotations
import httpx
from typing import Any, Dict, Optional
from mailing.config import settings
from mailing.logging_config import logger
from .retry import with_retry  # переиспользуем общую retry функцию
from .rate_limiter import get_resend_limiter

class ResendError(RuntimeError):
    def __init__(self, message: str, *, status_code: Optional[int] = None, retry_after: Optional[float] = None, retriable: Optional[bool] = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after
        # По умолчанию считаем ретрайным только 429 и 5xx, остальное — нет
        if retriable is None:
            self.retriable = (status_code == 429) or (isinstance(status_code, int) and 500 <= status_code <= 599)
        else:
            self.retriable = retriable

class ResendClient:
    """Клиент Resend API.

    Документация: https://resend.com/docs/api-reference/emails/send-email
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: float = 30.0):
        self.api_key = api_key or settings.resend_api_key
        if not self.api_key:
            raise RuntimeError("RESEND_API_KEY is not configured")
        self.base_url = (base_url or settings.resend_base_url).rstrip('/')
        self._client = httpx.AsyncClient(timeout=timeout, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    async def close(self):
        await self._client.aclose()

    async def send_message(self, *, to: str, subject: str, html: str, text: Optional[str] = None, sender: Optional[str] = None) -> Dict[str, Any]:
        """Отправка письма через Resend API. Возвращает dict ответа.

        Поле to — одиночный email; библиотека оборачивает его в список для API.
        """
        limiter = get_resend_limiter()

        async def _call():
            async with limiter:
                payload: Dict[str, Any] = {
                    "from": sender or settings.sender_email or "no-reply@example.com",
                    "to": [to],
                    "subject": subject,
                    "html": html,
                }
                if text:  # опционально — Resend сам сгенерирует, если не указано
                    payload["text"] = text
                url = f"{self.base_url}/emails"
                resp = await self._client.post(url, json=payload)
                retry_after_header = resp.headers.get("Retry-After")
                retry_after: Optional[float] = None
                if retry_after_header:
                    try:
                        retry_after = float(retry_after_header)
                    except ValueError:
                        retry_after = None
                sc = resp.status_code
                if sc in (500, 502, 503, 504):
                    raise ResendError(f"Transient {sc}: {resp.text[:200]}", status_code=sc, retry_after=retry_after)
                if sc == 429:
                    raise ResendError(f"Rate limited 429: {resp.text[:200]}", status_code=sc, retry_after=retry_after)
                if sc == 401:
                    raise ResendError("Unauthorized (401) — check RESEND_API_KEY", status_code=sc, retriable=False)
                if sc == 422:
                    raise ResendError(f"Validation error 422: {resp.text[:200]}", status_code=sc, retriable=False)
                if not resp.is_success:
                    raise ResendError(f"Resend error {sc}: {resp.text[:200]}", status_code=sc, retriable=False)
                data = resp.json()
                # Ожидается поле id (например: "id": "xxxx")
                if "id" not in data:
                    logger.warning("Resend response missing id field: %s", data)
                return data
        # Отдельно можем настроить retries: 429 + 5xx => exponential backoff
        return await with_retry(_call, retries=settings.max_retries)

__all__ = ["ResendClient", "ResendError"]
