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
Поддерживает retry логику, rate limiting и комплексную обработку ошибок."""

class ResendError(RuntimeError):"""
"""Класс ResendError."""
    Исключение для ошибок Resend API.

    Содержит дополнительную информацию о статус коде, времени повтора
    и возможности retry операции."""

    def __init__(
    """Инициализирует объект."""
    self,
    message: str,
    *,
    status_code: Optional[int] = None,
    retry_after: Optional[float] = None,retriable: Optional[bool] = None,"
        ") -> None:"""
    Инициализирует исключение Resend API.

    Args:
        message: Описание ошибки
        status_code: HTTP статус код ответа API
        retry_after: Время в секундах до возможного повтора
        retriable: Можно ли повторить запрос (auto-detect если None)"""
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

class ResendClient:"""
    """Класс ResendClient."""
    Асинхронный клиент для Resend Email API.

    Предоставляет высокоуровневый интерфейс для отправки email через Resend API
    с автоматическим retry, rate limiting и обработкой ошибок.

    Документация API: https://resend.com/docs/api-reference/emails/send-email

    Attributes:
    api_key: API ключ для аутентификации в Resend
    base_url: Базовый URL Resend API
    _client: Внутренний HTTP клиент"""

    def __init__(
    """Инициализирует объект."""
    self,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,timeout: float = 30.0,"
        ") -> None:"""
    Инициализирует Resend клиент.

    Args:
        api_key: API ключ (по умолчанию из настроек)
        base_url: Базовый URL API (по умолчанию из настроек)
        timeout: Таймаут для HTTP запросов в секундах

    Raises:
        RuntimeError: Если RESEND_API_KEY не настроен"""
    self.api_key = api_key or settings.resend_api_key
        if not self.api_key:raise RuntimeError("RESEND_API_KEY is not configured")self.base_url = (base_url or settings.resend_base_url).rstrip("/")
    self._client = httpx.AsyncClient(timeout = timeout,"
        "headers={"Authorization": f"Bearer {self.api_key}","""Content-Type": "application/json","""Accept": "application/json""},"
        ")

    async def close(self) -> None:"""
    """Выполняет close."""
    Закрывает HTTP клиент и освобождает ресурсы.

    Должен быть вызван после завершения работы с клиентом
    для корректного освобождения соединений."""
    await self._client.aclose()

    async def send_message(
    """Выполняет send message."""
    self,
    *,
    to: str,
    subject: str,
    html: str,
    text: Optional[str] = None,sender: Optional[str] = None,"
        ") -> Dict[str, Any]:"""
    Отправляет email сообщение через Resend API.
Выполняет полную отправку email с валидацией входных данных,"
        "rate limiting, retry логикой и комплексной обработкой ошибок.

    Args:
        to: Email адрес получателя (одиночный адрес)
        subject: Тема письма (не может быть пустой)
        html: HTML содержимое письма (обязательно)
        text: Опциональное текстовое содержимое (auto-генерируется если не указано)
        sender: Опциональный отправитель (по умолчанию из конфигурации)

    Returns:
        Dict[str, Any]: Ответ Resend API, содержащий 'id' отправленного сообщения

    Raises:
        ValueError: При некорректных входных данных (пустые поля)
        ResendError: При ошибках API (rate limits, server errors, auth issues)

    Example:
        response = await client.send_message(
            to="user@example.com",""subject="Welcome!",""html="<h1>Hello World</h1>",""text="Hello World"
        )
        message_id = response['id']
    """
    # Валидация входных данных
        if not to or not to.strip():raise ValueError("Email получателя не может быть пустым")
        if not subject or not subject.strip():raise ValueError("Тема письма не может быть пустой")
        if not html or not html.strip():raise ValueError("HTML содержимое не может быть пустым")

    limiter = get_resend_limiter()

        async def _call():
    """Внутренний метод для call."""
    """Выполняет  call."""
            async with limiter:
            # Resend requires a verified sender domain. Prefer configured Resend sender.
            default_from = (f"{settings.resend_from_name} <{settings.resend_from_email}>"
                    if settings.resend_from_name
                else settings.resend_from_email
            )
            payload: Dict[str, Any] = {"from": sender or default_from,"""to": [to],"""subject": subject,"""html": html,""}
                if text:  # опционально — Resend сам сгенерирует, если не указано
                payload["text"] = text
                if settings.list_unsubscribe:
                # RFC 2369 header; Resend header passthrough: https://resend.com/docs/api-reference/emails/send-emailpayload.setdefault("headers", {})payload["headers"]["List-Unsubscribe"] = settings.list_unsubscribeurl = f"{self.base_url}/emails"
            resp = await self._client.post(url, json = payload)retry_after_header = resp.headers.get("Retry-After")
            retry_after: Optional[float] = None
                if retry_after_header:
                    try:
                    retry_after = float(retry_after_header)
                    except ValueError:
                    retry_after = None
            sc = resp.status_code

            # Константы для лучшей читаемости
            SERVER_ERROR_CODES = (500, 502, 503, 504)
            RATE_LIMIT_CODE = 429
            UNAUTHORIZED_CODE = 401
            VALIDATION_ERROR_CODE = 422
            MAX_ERROR_LENGTH = 200

            # Безопасное получение текста ошибки (защита от Mock объектов)
                try:
                error_text = str(resp.text)[:MAX_ERROR_LENGTH]
                except (TypeError, AttributeError):error_text = "Unable to get error text"

                if sc in SERVER_ERROR_CODES:
                raise ResendError(f"Server error {sc}: {error_text}",
                    status_code = sc,retry_after = retry_after,"
        ")
                elif sc == RATE_LIMIT_CODE:
                raise ResendError(f"Rate limited: {error_text}",
                    status_code = sc,retry_after = retry_after,"
        ")
                elif sc == UNAUTHORIZED_CODE:
                raise ResendError("Unauthorized - check RESEND_API_KEY",
                    status_code = sc,retriable = False,"
        ")
                elif sc == VALIDATION_ERROR_CODE:
                raise ResendError(f"Validation error: {error_text}",
                    status_code = sc,retriable = False,"
        ")
                elif not resp.is_success:
                raise ResendError(f"Resend API error {sc}: {error_text}",
                    status_code = sc,retriable = False,"
        ")
                data = resp.json()# Ожидается поле id (например: "id": "xxxx")if "id" not in data:logger.warning("Resend response missing id field: %s", data)
                return data

    # Отдельно можем настроить retries: 429 + 5xx => exponential backoff
        return await with_retry(_call, retries = settings.max_retries)

__all__ = ["ResendClient", "ResendError"]
