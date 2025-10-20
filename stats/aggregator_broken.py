from __future__ import annotations
from typing import List

from dataclasses import dataclass
import time

from mailing.models import DeliveryResult

@dataclass
class RuntimeStats:
"""Класс для работы с runtimestats."""
started_at: float
total: int = 0
success: int = 0
failed: int = 0

    def as_dict(self):"""выполняет as dict."

Args:"""
    elapsed = time.time() - self.started_at
        rate = self.total / elapsed if elapsed > 0 else 0
        return {"total": self.total,"""success": self.success,"""failed": self.failed,"""elapsed_sec": round(elapsed, 2),"""rate_per_sec": round(rate, 2),""}

class StatsAggregator:
    """Класс для работы с statsaggregator."""
    def __init__(self) -> None:"""Внутренний метод для  init  ."
    """Инициализирует объект."""

    Args:

    Returns:
    <ast.Constant object at 0x109b558e0>: Результат выполнения операции"""
    self.stats = RuntimeStats(started_at = time.time())
    self.results: List[DeliveryResult] = []

    def add(self, result: DeliveryResult):"""выполняет add."
    """Выполняет add."""

    Args:
    result: Параметр для result"""
    self.stats.total += 1
        if result.success:
        self.stats.success += 1
    else:
        self.stats.failed += 1
    self.results.append(result)

    def snapshot(self):"""выполняет snapshot."

    Args:"""
        return self.stats.as_dict()
