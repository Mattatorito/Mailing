from __future__ import annotations
import asyncio
import threading
from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal
from mailing.sender import run_campaign, CampaignController
from mailing.models import Recipient

class MailerService(QObject):
    """Обёртка запуска run_campaign в отдельном потоке с asyncio loop.
    Сигналы потокобезопасны для GUI.
    """
    started = Signal()
    progress = Signal(dict)   # event dict (type=progress, result, stats)
    finished = Signal(dict)   # stats snapshot
    error = Signal(str, dict) # message, stats
    cancelled = Signal(dict)  # stats

    def __init__(self):
        super().__init__()
        self._thread: Optional[threading.Thread] = None
        self._controller: Optional[CampaignController] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.Lock()

    def is_running(self) -> bool:
        return self._running

    def start(self, *, recipients: List[Recipient], template_name: str, subject: str, dry_run: bool, concurrency: int) -> bool:
        with self._lock:
            if self._running:
                return False
            self._running = True
        self._controller = CampaignController()
        self._thread = threading.Thread(target=self._thread_main, args=(recipients, template_name, subject, dry_run, concurrency), daemon=True)
        self._thread.start()
        self.started.emit()
        return True

    def cancel(self):
        if self._controller:
            self._controller.cancel()

    # ---- internal ----
    def _thread_main(self, recipients: List[Recipient], template_name: str, subject: str, dry_run: bool, concurrency: int):
        try:
            asyncio.run(self._runner(recipients, template_name, subject, dry_run, concurrency))
        finally:
            with self._lock:
                self._running = False

    async def _runner(self, recipients: List[Recipient], template: str, subject: str, dry_run: bool, concurrency: int):
        assert self._controller is not None
        try:
            async for event in run_campaign(
                recipients=recipients,
                template_name=template,
                subject=subject,
                dry_run=dry_run,
                concurrency=concurrency,
                controller=self._controller,
            ):
                et = event.get('type')
                if et == 'progress':
                    self.progress.emit(event)
                elif et == 'finished':
                    self.finished.emit(event.get('stats', {}))
                elif et == 'error':
                    if event.get('error') == 'cancelled':
                        self.cancelled.emit(event.get('stats', {}))
                    else:
                        self.error.emit(str(event.get('error')), event.get('stats', {}))
        except Exception as e:  # noqa
            self.error.emit(str(e), {})
