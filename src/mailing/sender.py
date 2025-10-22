#!/usr/bin/env python3

from __future__ import annotations
from typing import AsyncIterator, Optional, Dict, Any, List
import asyncio

from src.mailing.limits.daily_quota import DailyQuota
from src.mailing.logging_config import logger
from src.mailing.models import Recipient, DeliveryResult
from src.persistence.repository import DeliveryRepository, SuppressionRepository
from src.resend.client import ResendClient, ResendError
from src.stats.aggregator import StatsAggregator
from src.templating.engine import TemplateEngine


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
            if controller.is_cancelled:
                raise CampaignCancelled()
            
            # Проверка квоты перед отправкой
            if not dry_run and quota.is_exceeded():
                logger.warning(f"Daily quota exceeded, skipping {recipient.email}")
                result = DeliveryResult(
                    email=recipient.email,
                    success=False,
                    status_code=0,
                    error="quota_exceeded",
                    provider="resend"
                )
                repo.save_delivery(result)
                return result
            
            # Проверка подавлений
            if not dry_run:
                if suppressions.is_unsubscribed(recipient.email):
                    result = DeliveryResult(
                        email=recipient.email,
                        success=False,
                        status_code=0,
                        error="unsubscribed",
                        provider="resend"
                    )
                    # Сохраняем результат проверки suppression
                    repo.save_delivery(result)
                    return result
                
                if suppressions.is_suppressed(recipient.email):
                    result = DeliveryResult(
                        email=recipient.email,
                        success=False,
                        status_code=0,
                        error="suppressed",
                        provider="resend"
                    )
                    # Сохраняем результат проверки suppression
                    repo.save_delivery(result)
                    return result
            
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
                
                # Регистрируем в квоте только успешные доставки
                if result.success and not dry_run:
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
    
    # Запуск всех задач с timeout
    worker_timeout = 60  # 60 секунд на отправку одного письма
    pending_tasks = set()
    
    try:
        tasks = [asyncio.create_task(worker(recipient)) for recipient in recipients]
        pending_tasks.update(tasks)
        
        for coro in asyncio.as_completed(tasks, timeout=worker_timeout * len(recipients)):
            try:
                result = await asyncio.wait_for(coro, timeout=worker_timeout)
                pending_tasks.discard(coro)
                stats.add(result)
                
                yield {
                    "type": "progress",
                    "result": result,
                    "stats": stats.snapshot()
                }
                
            except asyncio.TimeoutError:
                logger.warning("Worker task timed out")
                yield {
                    "type": "error", 
                    "message": "Worker task timed out",
                    "stats": stats.snapshot()
                }
                # Отменяем оставшиеся задачи при timeout
                for task in pending_tasks:
                    if not task.done():
                        task.cancel()
                return
                
            except CampaignCancelled:
                logger.info("Campaign cancelled")
                # Отменяем все оставшиеся задачи
                for task in pending_tasks:
                    if not task.done():
                        task.cancel()
                        
                yield {
                    "type": "error",
                    "message": "Campaign cancelled", 
                    "stats": stats.snapshot()
                }
                return
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                # Отменяем оставшиеся задачи при ошибке
                for task in pending_tasks:
                    if not task.done():
                        task.cancel()
                        
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
        
    except asyncio.TimeoutError:
        logger.error("Overall campaign timeout")
        # Отменяем все оставшиеся задачи
        for task in pending_tasks:
            if not task.done():
                task.cancel()
                
        yield {
            "type": "error",
            "message": "Campaign timeout",
            "stats": stats.snapshot()
        }
        
    except Exception as e:
        logger.error(f"Campaign error: {e}")
        # Отменяем все оставшиеся задачи
        for task in pending_tasks:
            if not task.done():
                task.cancel()
                
        yield {
            "type": "error",
            "message": str(e),
            "stats": stats.snapshot()
        }
