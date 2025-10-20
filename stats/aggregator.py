from __future__ import annotations
from typing import Dict, Any
from datetime import datetime
from collections import defaultdict


class StatsAggregator:
    """Агрегатор статистики для email кампаний."""
    
    def __init__(self):
        """Инициализирует агрегатор статистики."""
        self.results = []
        self.start_time = datetime.now()
    
    def add(self, result) -> None:
        """Добавляет результат доставки в статистику.
        
        Args:
            result: Объект DeliveryResult
        """
        self.results.append(result)
    
    def snapshot(self) -> Dict[str, Any]:
        """Возвращает текущий снимок статистики.
        
        Returns:
            Словарь со статистикой
        """
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        failed = total - success
        
        # Статистика по провайдерам
        by_provider = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0})
        for result in self.results:
            provider = result.provider or "unknown"
            by_provider[provider]["total"] += 1
            if result.success:
                by_provider[provider]["success"] += 1
            else:
                by_provider[provider]["failed"] += 1
        
        # Время выполнения
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "elapsed_seconds": elapsed,
            "by_provider": dict(by_provider),
        }
    
    def reset(self) -> None:
        """Сбрасывает статистику."""
        self.results.clear()
        self.start_time = datetime.now()