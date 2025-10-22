from __future__ import annotations
import asyncio
from typing import AsyncIterator, Iterable, Optional, Dict, Any, List
from templating.engine import TemplateEngine
from resend.client import ResendClient, ResendError
from mailing.config import settings
from persistence.repository import DeliveryRepository
from stats.aggregator import StatsAggregator
from mailing.models import Recipient, DeliveryResult
from mailing.logging_config import logger
from mailing.limits.daily_quota import DailyQuota

class CampaignCancelled(Exception):
    pass

class CampaignController:
    def __init__(self):
        self._cancel = False
    def cancel(self):
        self._cancel = True
    def cancelled(self) -> bool:
        return self._cancel

async def run_campaign(*, recipients: List[Recipient], template_name: str, subject: str, dry_run: bool, concurrency: int, controller: Optional[CampaignController] = None) -> AsyncIterator[Dict[str, Any]]:
    """
    Асинхронный генератор событий кампании.
    yield dict(type='progress'|'finished'|'error', ...)
    """
    engine = TemplateEngine()
    repo = DeliveryRepository()
    stats = StatsAggregator()
    # Выбор провайдера с учётом FORCE_PROVIDER
    client: ResendClient
    # Теперь единственный провайдер — Resend. FORCE_PROVIDER и fallback удалены.
    client = ResendClient()
    reason = "resend-only"
    logger.info("Провайдер: Resend (%s)", reason)
    sem = asyncio.Semaphore(concurrency)
    quota = DailyQuota()
    quota.load()
    controller = controller or CampaignController()

    async def worker(recipient: Recipient):
        async with sem:
            if controller.cancelled():
                raise CampaignCancelled()
            # Проверка дневного лимита (не считаем dry-run)
            if not dry_run:
                if not quota.can_send():
                    logger.warning("Достигнут дневной лимит отправок (%d/%d)", quota.used(), quota.limit)
                    return DeliveryResult(email=recipient.email, success=False, status_code=0, error="daily-limit")
            render = engine.render(template_name, {**recipient.variables, 'email': recipient.email, 'subject': subject})
            if dry_run:
                result = DeliveryResult(email=recipient.email, success=True, status_code=0, message_id="dry-run", provider="dry-run")
            else:
                try:
                    quota.register()
                    resp = await client.send_message(to=recipient.email, subject=render.subject, html=render.body_html)
                    # Resend: id – сохраняем как message_id
                    msg_id = resp.get('id') if isinstance(resp, dict) else None
                    provider_name = 'resend'
                    result = DeliveryResult(email=recipient.email, success=True, status_code=200, message_id=msg_id, provider=provider_name)
                except Exception as e:  # noqa
                    provider_name = 'resend'
                    result = DeliveryResult(email=recipient.email, success=False, status_code=0, error=str(e), provider=provider_name)
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
        await client.close()
