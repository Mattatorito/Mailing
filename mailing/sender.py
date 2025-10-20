from __future__ import annotations
from typing import AsyncIterator, Iterable, Optional, Dict, Any, List
import asyncio

from mailing.config import settings
from mailing.limits.daily_quota import DailyQuota
from mailing.logging_config import logger
from mailing.models import Recipient, DeliveryResult
from persistence.repository import DeliveryRepository, SuppressionRepository
from resend.client import ResendClient, ResendError
from stats.aggregator import StatsAggregator
from templating.engine import TemplateEngine

"""
Email Campaign Sender Module

Этот модуль содержит основную логику отправки email кампаний.
Поддерживает асинхронную отправку через Resend API с контролем лимитов и статистикой."""


class CampaignCancelled(Exception):
    """Исключение для отмены выполнения кампании.

    Поднимается когда пользователь или система запрашивает досрочную остановку
    отправки email кампании.
    """
    pass


class CampaignController:
    """Контроллер для управления выполнением email кампании.

    Позволяет отменять кампанию во время её выполнения и проверять статус отмены.
    Используется для координации между UI и бэкенд процессами.
    """

    def __init__(self) -> None:
        """Инициализирует новый контроллер кампании."""
        self._cancel = False

    def cancel(self) -> None:
        """Отменяет выполнение кампании.

        После вызова этого метода, все активные задачи отправки должны быть остановлены.
        """
        self._cancel = True

    def cancelled(self) -> bool:
        """Проверяет, была ли запрошена отмена кампании.

        Returns:
            bool: True если кампания была отменена, False в противном случае
        """
        return self._cancel

    # Свойство для удобного доступа (как в тестах)
    @property
    def is_cancelled(self) -> bool:
        """Свойство для проверки статуса отмены кампании.
        
        Returns:
            bool: True если кампания была отменена, False в противном случае
        """
        return self._cancel


async def run_campaign(
    *,
    recipients: List[Recipient],
    template_name: str,
    subject: str,
    dry_run: bool,
    concurrency: int,
    controller: Optional[CampaignController] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """Запускает асинхронную email кампанию с поддержкой отмены и мониторинга прогресса.

    Основная функция для отправки массовых email сообщений. Поддерживает:
    - Асинхронную отправку с контролем конкурентности
    - Dry-run режим для тестирования без реальной отправки
    - Отслеживание прогресса через yield события
    - Контроль дневных лимитов и подавления адресов
    - Graceful отмену кампании

    Args:
        recipients: Список получателей с email адресами и переменными шаблона
        template_name: Имя шаблона email для рендеринга
        subject: Тема письма (может содержать переменные шаблона)
        dry_run: Если True, выполняет симуляцию без реальной отправки
        concurrency: Максимальное количество параллельных отправок
        controller: Опциональный контроллер для отмены кампании

    Yields:
        Dict[str, Any]: События прогресса кампании с типами:
            - 'progress': Результат отправки одного письма + статистика- 'finished': Завершение кампании + итоговая статистика- 'error': Ошибка (например, отмена кампании)

    Raises:
        CampaignCancelled: Когда кампания отменена через controller

    Example:
        async for event in run_campaign(
            recipients=[Recipient(email="user@example.com",variables={})],
                template_name="welcome",subject="Welcome!",
            dry_run = False,
            concurrency = 10
        ):
            if event['type'] == 'progress':
                print(f"Sent to {event['result'].email}")
            elif event['type'] == 'finished':
                print(f"Campaign completed: {event['stats']}")
    """
    logger.info(
        "Starting campaign: recipients=%d, template=%s, subject=%s, dry_run=%s, concurrency=%d",
        len(recipients),
        template_name,
        subject,
        dry_run,
        concurrency,
    )

    engine = TemplateEngine()
    repo = DeliveryRepository()
    suppressions = SuppressionRepository()
    stats = StatsAggregator()
    # Выбор провайдера с учётом FORCE_PROVIDER
    client: ResendClient
    # Теперь единственный провайдер — Resend. FORCE_PROVIDER и fallback удалены.
    client = ResendClient()
    reason = "resend-only"
    logger.info("Email provider: Resend (%s)", reason)
    
    sem = asyncio.Semaphore(concurrency)
    quota = DailyQuota()
    quota.load()
    controller = controller or CampaignController()

    async def worker(recipient: Recipient):
        """Асинхронный worker для обработки одного получателя."""
        async with sem:
            if controller.cancelled():
                raise CampaignCancelled()
                
            # Проверка дневного лимита (не считаем dry-run)
            if not dry_run:
                # Отписки/блок-лист
                if suppressions.is_unsubscribed(recipient.email):
                    return DeliveryResult(
                        email=recipient.email,
                        success=False,
                        status_code=0,
                        error="unsubscribed",
                        provider="resend",
                    )
                if suppressions.is_suppressed(recipient.email):
                    return DeliveryResult(
                        email=recipient.email,
                        success=False,
                        status_code=0,
                        error="suppressed",
                        provider="resend",
                    )
                if not quota.can_send():
                    logger.warning(
                        "Достигнут дневной лимит отправок (%d/%d)",
                        quota.used(),
                        quota.limit,
                    )
                    return DeliveryResult(
                        email=recipient.email,
                        success=False,
                        status_code=0,
                        error="daily-limit",
                        provider="resend",
                    )
            
            try:
                render = engine.render(
                    template_name,
                    {
                        **recipient.variables,
                        "email": recipient.email,
                        "subject": subject,
                    },
                )
            except Exception as e:
                logger.error(f"Template render error for {recipient.email}: {e}")
                return DeliveryResult(
                    email=recipient.email,
                    success=False,
                    status_code=0,
                    error=f"template-error: {e}",
                    provider="resend",
                )
            
            if not dry_run and (
                not render.subject or render.subject.strip().lower() in {"no subject", ""}
            ):
                return DeliveryResult(
                    email=recipient.email,
                    success=False,
                    status_code=0,
                    error="empty-subject",
                    provider="resend",
                )
            
            if dry_run:
                result = DeliveryResult(
                    email=recipient.email,
                    success=True,
                    status_code=200,
                    message_id="dry-run",
                    provider="dry-run",
                )
            else:
                try:
                    quota.register()
                    resp = await client.send_message(
                        to=recipient.email,
                        subject=render.subject,
                        html=render.body_html,
                        text=render.body_text,
                    )
                    # Resend: id – сохраняем как message_id
                    msg_id = resp.get("id") if isinstance(resp, dict) else None
                    provider_name = "resend"
                    result = DeliveryResult(
                        email=recipient.email,
                        success=True,
                        status_code=200,
                        message_id=msg_id,
                        provider=provider_name,
                    )
                except Exception as e:
                    provider_name = "resend"
                    result = DeliveryResult(
                        email=recipient.email,
                        success=False,
                        status_code=0,
                        error=str(e),
                        provider=provider_name,
                    )
            
            stats.add(result)
            repo.save(result)
            try:
                logger.info(
                    "deliver email=%s provider=%s success=%s status=%s used=%s remaining=%s limit=%s error=%s",
                    result.email,
                    result.provider,
                    result.success,
                    result.status_code,
                    quota.used(),
                    quota.remaining(),
                    quota.limit,
                    (result.error or "-"),
                )
            except Exception:  # noqa
                pass
            return result

    tasks: List[asyncio.Task] = []
    try:
        for rec in recipients:
            t = asyncio.create_task(worker(rec))
            tasks.append(t)
        completed = 0
        for t in asyncio.as_completed(tasks):
            try:
                res = await t
                snap = stats.snapshot()
                # дополняем статистику данными о дневном лимите
                try:
                    snap["daily_used"] = quota.used()
                    snap["daily_remaining"] = quota.remaining()
                    snap["daily_limit"] = quota.limit
                except Exception:
                    pass
                yield {"type": "progress", "result": res, "stats": snap}
                completed += 1
            except CampaignCancelled:
                logger.info("Кампания отменена")
                for pt in tasks:
                    pt.cancel()
                yield {"type": "error", "error": "cancelled", "stats": stats.snapshot()}
                break
        else:
            # normal finish
            snap = stats.snapshot()
            try:
                snap["daily_used"] = quota.used()
                snap["daily_remaining"] = quota.remaining()
                snap["daily_limit"] = quota.limit
            except Exception:
                pass
            yield {"type": "finished", "stats": snap}
    finally:
        # Безопасное закрытие клиента (защита от Mock объектов)
        try:
            if hasattr(client, "close") and callable(getattr(client, "close")):
                close_method = getattr(client, "close")
                # Проверяем что это корутина или обычный метод
                if hasattr(close_method, "__await__") or asyncio.iscoroutinefunction(
                    close_method
                ):
                    await close_method()
                elif callable(close_method):
                    close_method()
        except (TypeError, AttributeError):
            pass  # Ignore mock objects
