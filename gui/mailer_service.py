from PySide6.QtCore import QObject, Signal
from __future__ import annotations
from typing import List, Optional, Dict, Any
import asyncio
import threading

from mailing.models import Recipient
from mailing.sender import run_campaign, CampaignController

class MailerService(QObject):
"""Обёртка запуска run_campaign в отдельном потоке с asyncio loop.
Сигналы потокобезопасны для GUI."""

started = Signal()
progress = Signal(dict)  # event dict (type = progress, result, stats)
finished = Signal(dict)  # stats snapshot
error = Signal(str, dict)  # message, stats
cancelled = Signal(dict)  # stats

    def __init__(self):"""Внутренний метод для  init  .

    Args:"""
    super().__init__()
    self._thread: Optional[threading.Thread] = None
    self._controller: Optional[CampaignController] = None
    self._running = False
    self._loop: Optional[asyncio.AbstractEventLoop] = None
    self._lock = threading.Lock()

    def is_running(self) -> bool:"""выполняет is running.
    """Выполняет is running."""

    Args:

    Returns:
    bool: Результат выполнения операции"""
        return self._running

    def start("""выполняет start.
    """Выполняет start."""

    Args:

    Returns:
    bool: Результат выполнения операции"""
    self,
    *,
    recipients: List[Recipient],
    template_name: str,
    subject: str,
    dry_run: bool,
    concurrency: int,
    ) -> bool:
        with self._lock:
            if self._running:
                return False
        self._running = True
    self._controller = CampaignController()
    self._thread = threading.Thread(
        target = self._thread_main,
        args=(recipients,template_name,subject,dry_run,concurrency),daemon = True,"
        ")
    self._thread.start()
    self.started.emit()
        return True

    def cancel(self):"""выполняет cancel.

    Args:"""
        if self._controller:
        self._controller.cancel()

    # ---- internal ----
    def _thread_main("""Внутренний метод для thread main.
    """Выполняет  thread main."""

    Args:
    recipients: Параметр для recipients
    template_name: Параметр для template name
    subject: Параметр для subject
    dry_run: Параметр для dry run
    concurrency: Параметр для concurrency"""
    self,
    recipients: List[Recipient],
    template_name: str,
    subject: str,
    dry_run: bool,concurrency: int,"
        "):
        try:
        asyncio.run(
            self._runner(recipients, template_name, subject, dry_run, concurrency)
        )
    finally:
            with self._lock:
            self._running = False

    async def _runner("""Внутренний метод для runner.
    """Выполняет  runner."""

    Args:
    recipients: Параметр для recipients
    template: Параметр для template
    subject: Параметр для subject
    dry_run: Параметр для dry run
    concurrency: Параметр для concurrency"""
    self,
    recipients: List[Recipient],
    template: str,
    subject: str,
    dry_run: bool,
    concurrency: int,
    ):
    assert self._controller is not None
        try:
            async for event in run_campaign(
            recipients = recipients,
            template_name = template,
            subject = subject,
            dry_run = dry_run,
            concurrency = concurrency,controller = self._controller,"
            "):et = event.get("type")if et == "progress":
                    self.progress.emit(event)elif et == "finished":self.finished.emit(event.get("stats",
                        {}))elif et == "error":if event.get("error") == "cancelled":self.cancelled.emit(event.get("stats", {}))
                else:self.error.emit(str(event.get("error")),event.get("stats", {}))
        except Exception as e:  # noqa
        self.error.emit(str(e), {})
