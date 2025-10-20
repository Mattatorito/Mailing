#!/usr/bin/env python3

from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json


class StatsAggregator:
    """Агрегатор статистики для email кампаний."""
    
    def __init__(self):
        """Инициализирует агрегатор."""
        self.stats = {
            'sent': 0,
            'delivered': 0,
            'failed': 0,
            'bounced': 0,
            'opened': 0,
            'clicked': 0,
            'unsubscribed': 0
        }
        self.events: List[Dict[str, Any]] = []
    
    def add_event(self, event_type: str, email: str = "", **kwargs):
        """Добавляет событие в статистику."""
        event = {
            'type': event_type,
            'email': email,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self.events.append(event)
        
        if event_type in self.stats:
            self.stats[event_type] += 1
    
    def increment(self, stat_name: str, count: int = 1):
        """Увеличивает счетчик статистики."""
        if stat_name in self.stats:
            self.stats[stat_name] += count
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает текущую статистику."""
        return {
            **self.stats,
            'total_events': len(self.events),
            'success_rate': self._calculate_success_rate(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _calculate_success_rate(self) -> float:
        """Вычисляет процент успешных доставок."""
        total = self.stats['sent']
        if total == 0:
            return 0.0
        delivered = self.stats['delivered']
        return round((delivered / total) * 100, 2)
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Возвращает события по типу."""
        return [event for event in self.events if event['type'] == event_type]
    
    def get_events_by_timeframe(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Возвращает события за последние N часов."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            event for event in self.events 
            if datetime.fromisoformat(event['timestamp']) >= cutoff
        ]
    
    def export_stats(self) -> str:
        """Экспортирует статистику в JSON."""
        return json.dumps(self.get_stats(), indent=2, ensure_ascii=False)
    
    def reset(self):
        """Сбрасывает всю статистику."""
        self.stats = {
            'sent': 0,
            'delivered': 0,
            'failed': 0,
            'bounced': 0,
            'opened': 0,
            'clicked': 0,
            'unsubscribed': 0
        }
        self.events.clear()
