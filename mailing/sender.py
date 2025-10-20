#!/usr/bin/env python3

from __future__ import annotations
from typing import AsyncIterator, Optional, Dict, Any, List
import asyncio

from mailing.limits.daily_quota import DailyQuota
from mailing.logging_config import logger
from mailing.models import Recipient, DeliveryResult
from persistence.repository import DeliveryRepository, SuppressionRepository
from resend.client import ResendClient, ResendError
from stats.aggregator import StatsAggregator
from templating.engine import TemplateEngine


class CampaignCancelled(Exception):
    """Исключение для отмены выполнения кампании."""
    pass


class CampaignController:
    """Контроллер для управления выполнением email кампании."""
    
    def __init__(self) -> None:
        """Инициализирует новый контроллер кампании."""
        self._cancel = False

    def cancel(self) -> None:
        """Отменяет выполнение кампании."""
        self._cancel = True

    def cancelled(self) -> bool:
        """Проверяет, была ли запрошена отмена кампании."""
        return self._cancel

    @property
    def is_cancelled(self) -> bool:
        """Свойство для проверки статуса отмены кампании."""
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
    """Запускает email кампанию."""
    
    logger.info(
        "Starting campaign: recipients=%d, template=%s, subject=%s, dry_run=%s, concurrency=%d",
        len(recipients), template_name, subject, dry_run, concurrency
    )
    
    engine = TemplateEngine()
    repo = DeliveryRepository()
    suppressions = SuppressionRepository()
    stats = StatsAggregator()
    
    # Настройка клиента
    client = ResendClient()
    logger.info("Email provider: Resend (resend-only)")
    
    sem = asyncio.Semaphore(concurrency)
    quota = DailyQuota()
    quota.load()
    controller = controller or CampaignController()
    
    async def worker(recipient: Recipient):
        """Асинхронный worker для обработки одного получателя."""
        async with sem:
            if controller.cancelled():
                raise CampaignCancelled()
            
            # Проверка подавлений
            if not dry_run:
                if suppressions.is_unsubscribed(recipient.email):
                    return DeliveryResult(
                        email=recipient.email,
                        success=False,
                        status_code=0,
                        error="unsubscribed",
                        provider="resend"
                    )
                
                if suppressions.is_suppressed(recipient.email):
                    return DeliveryResult(
                        email=recipient.email,
                        success=False,
                        status_code=0,
                        error="suppressed",
                        provider="resend"
                    )
            
            try:
                # Рендеринг шаблона
                html_content, text_content = engine.render(template_name, recipient.variables)
                
                if dry_run:
                    # Симуляция отправки
                    await asyncio.sleep(0.1)  # Имитация задержки
                    result = DeliveryResult(
                        email=recipient.email,
                        success=True,
                        status_code=200,
                        provider="dry-run"
                    )
                else:
                    # Реальная отправка
                    result = await client.send_message(
                        to_email=recipient.email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content
                    )
                
                # Сохранение в БД
                repo.save_delivery(result)
                quota.register()
                
                return result
                
            except Exception as e:
                logger.error(f"Error sending to {recipient.email}: {e}")
                result = DeliveryResult(
                    email=recipient.email,
                    success=False,
                    status_code=0,
                    error=str(e),
                    provider="resend"
                )
                repo.save_delivery(result)
                return result
    
    # Запуск всех задач
    try:
        tasks = [worker(recipient) for recipient in recipients]
        
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                stats.add(result)
                
                yield {
                    "type": "progress",
                    "result": result,
                    "stats": stats.snapshot()
                }
                
            except CampaignCancelled:
                logger.info("Campaign cancelled")
                yield {
                    "type": "error",
                    "message": "Campaign cancelled",
                    "stats": stats.snapshot()
                }
                return
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                yield {
                    "type": "error",
                    "message": str(e),
                    "stats": stats.snapshot()
                }
                return
        
        # Завершение кампании
        yield {
            "type": "finished",
            "stats": stats.snapshot()
        }
        
    except Exception as e:
        logger.error(f"Campaign error: {e}")
        yield {
            "type": "error",
            "message": str(e),
            "stats": stats.snapshot()
        }
