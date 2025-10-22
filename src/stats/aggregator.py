#!/usr/bin/env python3

from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import threading


class StatsAggregator:
    """Агрегатор статистики для email кампаний."""
    
    # Default stats structure - centralized definition
    DEFAULT_STATS = {
        'sent': 0,
        'delivered': 0,
        'failed': 0,
        'bounced': 0,
        'opened': 0,
        'clicked': 0,
        'unsubscribed': 0
    }
    
    def __init__(self):
        """Инициализирует агрегатор."""
        self.stats = self.DEFAULT_STATS.copy()
        self.events: List[Dict[str, Any]] = []
        self._lock = threading.RLock()  # Thread safety
    
    def add_event(self, event_type: str, email: str = "", **kwargs):
        """Добавляет событие в статистику."""
        # Validate event_type early to catch errors
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError(f"Invalid event_type: {event_type}. Must be a non-empty string.")
        
        # Validate that event_type is a known stat type
        if event_type not in self.DEFAULT_STATS:
            raise ValueError(f"Unknown event_type: {event_type}. Valid types: {list(self.DEFAULT_STATS.keys())}")
        
        event = {
            'type': event_type,
            'email': email,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        with self._lock:
            self.events.append(event)
            
            # Direct increment since we've already validated the event_type
            self.stats[event_type] += 1
    
    def increment(self, stat_name: str, count: int = 1):
        """Увеличивает счетчик статистики."""
        # Validate stat_name early to catch errors
        if not isinstance(stat_name, str) or not stat_name.strip():
            raise ValueError(f"Invalid stat_name: {stat_name}. Must be a non-empty string.")
        
        with self._lock:
            if stat_name in self.stats:
                self.stats[stat_name] += count
            else:
                raise ValueError(f"Unknown stat_name: {stat_name}. Valid names: {list(self.stats.keys())}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает текущую статистику."""
        with self._lock:
            return {
                **self.stats,
                'total_events': len(self.events),
                'success_rate': self._calculate_success_rate(),
                'last_updated': datetime.now().isoformat()
            }
    
    def snapshot(self) -> Dict[str, Any]:
        """Возвращает снимок текущей статистики (алиас для get_stats)."""
        return self.get_stats()
    
    def add(self, result) -> None:
        """Добавляет результат доставки в статистику."""
        # Increment 'sent' BEFORE processing delivery outcome
        self.increment('sent')
        
        if hasattr(result, 'success') and result.success:
            self.increment('delivered')
        else:
            self.increment('failed')
        
        # Добавляем событие
        self.add_event(
            'delivery',
            email=getattr(result, 'email', ''),
            success=getattr(result, 'success', False),
            status_code=getattr(result, 'status_code', 0),
            provider=getattr(result, 'provider', '')
        )
    
    def _calculate_success_rate(self) -> float:
        """Вычисляет процент успешных доставок."""
        total = self.stats['sent']
        if total == 0:
            return 0.0
        delivered = self.stats['delivered']
        return round(delivered / total, 4)  # Возвращаем долю, не процент
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Возвращает события по типу с оптимизацией для больших списков."""
        # Validate event_type early
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError(f"Invalid event_type: {event_type}")
        
        with self._lock:
            # Optimization: for large event lists (>1000), use generator comprehension
            # to avoid creating intermediate lists
            if len(self.events) > 1000:
                # Use generator for memory efficiency
                return [event for event in self.events if event.get('type') == event_type]
            else:
                # Standard list comprehension for smaller lists
                return [event for event in self.events if event['type'] == event_type]
    
    def get_events_by_timeframe(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Возвращает события за последние N часов с оптимизацией."""
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()
        
        with self._lock:
            # Optimization: for large event lists, use early termination
            # since events are typically ordered by timestamp
            if len(self.events) > 1000:
                result = []
                # Reverse iteration for recent events first
                for event in reversed(self.events):
                    event_time = event.get('timestamp', '')
                    if event_time >= cutoff_iso:
                        result.append(event)
                    elif event_time < cutoff_iso:
                        # Early termination if events are ordered
                        break
                return list(reversed(result))  # Restore chronological order
            else:
                # Standard filtering for smaller lists
                return [
                    event for event in self.events 
                    if event.get('timestamp', '') >= cutoff_iso
                ]
    
    def export_stats(self) -> str:
        """Экспортирует статистику в JSON."""
        return json.dumps(self.get_stats(), indent=2, ensure_ascii=False)
    
    def reset(self):
        """Сбрасывает всю статистику."""
        with self._lock:
            self.stats = self.DEFAULT_STATS.copy()
            self.events.clear()
