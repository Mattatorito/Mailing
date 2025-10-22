from __future__ import annotations
import time
from dataclasses import dataclass
from mailing.models import DeliveryResult
from typing import List

@dataclass
class RuntimeStats:
    started_at: float
    total: int = 0
    success: int = 0
    failed: int = 0

    def as_dict(self):
        elapsed = time.time() - self.started_at
        rate = self.total / elapsed if elapsed > 0 else 0
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "elapsed_sec": round(elapsed, 2),
            "rate_per_sec": round(rate, 2),
        }

class StatsAggregator:
    def __init__(self) -> None:
        self.stats = RuntimeStats(started_at=time.time())
        self.results: List[DeliveryResult] = []

    def add(self, result: DeliveryResult):
        self.stats.total += 1
        if result.success:
            self.stats.success += 1
        else:
            self.stats.failed += 1
        self.results.append(result)

    def snapshot(self):
        return self.stats.as_dict()
