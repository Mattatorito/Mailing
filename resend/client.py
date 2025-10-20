from __future__ import annotations
from typing import Any, Dict, Optional
import httpx

from .rate_limiter import get_resend_limiter
from .retry import with_retry  # переиспользуем общую retry функцию
from mailing.config import settings
from mailing.logging_config import logger

"""
Resend API Client Module

Этот модуль предоставляет асинхронный клиент для работы с Resend Email API.
Поддерживает retry логику, rate limiting и комплексную обработку ошибок.
"""


class ResendError(RuntimeError):
    """Исключение для ошибок Resend API.

    Содержит дополнительную информацию о статус коде, времени повтора
    и возможности retry операции.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        retry_after: Optional[float] = None,
        retriable: Optional[bool] = None,
    ) -> None:
        """Инициализирует исключение Resend API.

        Args:
            message: Описание ошибки
            status_code: HTTP статус код ответа API
            retry_after: Время в секундах до возможного повтора
            retriable: Можно ли повторить запрос (auto-detect если None)
        """
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after
        # По умолчанию считаем ретрайным только 429 и 5xx, остальное — нет
        if retriable is None:
            self.retriable = (status_code == 429) or (
                isinstance(status_code, int) and 500 <= status_code <= 599
            )
        else:
            self.retriable = retriable


class ResendClient:
    """Асинхронный клиент для Resend Email API.

    Предоставляет высокоуровневый интерфейс для отправки email через Resend API
    с автоматическим retry, rate limiting и обработкой ошибок.

    Документация API: https://resend.com/docs/api-reference/emails/send-email
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """Инициализирует Resend клиент.

        Args:
            api_key: API ключ (по умолчанию из настроек)
            base_url: Базовый URL API (по умолчанию из настроек)
            timeout: Таймаут для HTTP запросов в секундах

        Raises:
            RuntimeError: Если RESEND_API_KEY не настроен
        """
        self.api_key = api_key or settings.resend_api_key
        if not self.api_key:
            raise RuntimeError("RESEND_API_KEY not configured")
        
        self.base_url = (base_url or settings.resend_base_url).rstrip("/")
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
        )

    async def close(self) -> None:
        """Закрывает HTTP клиент и освобождает ресурсы.

        Рекомендуется вызывать в finally блоке или использовать
        async context manager если он будет добавлен позже.
        """
        await self._client.aclose()

    async def send_message(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Отправляет email сообщение через Resend API.

        Args:
            to: Email получателя
            subject: Тема письма
            html: HTML содержимое письма
            text: Текстовая версия письма (опционально)
            sender: Отправитель (по умолчанию из настроек)

        Returns:
            Dict с ответом API, включая id сообщения

        Raises:
            ResendError: При ошибках API или валидации
        """
        # Валидация входных данных
        if not to or not to.strip():
            raise ResendError("Email получателя не может быть пустым")
        if not subject or not subject.strip():
            raise ResendError("Тема письма не может быть пустой")
        if not html or not html.strip():
            raise ResendError("HTML содержимое не может быть пустым")

        limiter = get_resend_limiter()

        async def _call():
            """Внутренний метод для отправки запроса."""
            async with limiter:
                # Resend requires a verified sender domain. Prefer configured Resend sender.
                default_from = (
                    f"{settings.resend_from_name} <{settings.resend_from_email}>"
                    if settings.resend_from_name
                    else settings.resend_from_email
                )
                payload: Dict[str, Any] = {
                    "from": sender or default_from,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                }
                
                if text:
                    payload["text"] = text

                logger.debug("Sending email via Resend API: to=%s subject=%s", to, subject)
                
                response = await self._client.post(
                    f"{self.base_url}/emails",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("Email sent successfully: to=%s id=%s", to, result.get("id"))
                    return result
                else:
                    error_body = response.text
                    logger.error("Resend API error: status=%d body=%s", response.status_code, error_body)
                    
                    # Определяем retry_after из заголовков
                    retry_after = None
                    if "retry-after" in response.headers:
                        try:
                            retry_after = float(response.headers["retry-after"])
                        except ValueError:
                            pass
                    
                    raise ResendError(
                        f"Resend API error: {response.status_code} {error_body}",
                        status_code=response.status_code,
                        retry_after=retry_after,
                    )

        # Отдельно можем настроить retries: 429 + 5xx => exponential backoff
        return await with_retry(_call, retries=settings.max_retries)


__all__ = ["ResendClient", "ResendError"]