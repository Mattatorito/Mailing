from __future__ import annotations
import asyncio

import pytest

from src.mailing.models import Recipient
from src.mailing.sender import run_campaign

@pytest.mark.asyncio
async def test_run_campaign_dry_run():
    """Тест для run campaign dry run."""
    recipients = [
        Recipient(email=f"u{i}@ex.com", variables={"name": f"User{i}"})
        for i in range(3)
    ]
    events = []
    async for ev in run_campaign(
        recipients=recipients,
        template_name="template.html",
        subject="Hello",
        dry_run=True,
        concurrency=2,
    ):
        events.append(ev["type"]) if "type" in ev else None

    assert "progress" in events
    assert "finished" in events
