from __future__ import annotations
from typing import Optional

from dataclasses import dataclass, field
from datetime import datetime, timezone, date

from mailing.config import settings
from persistence.db import get_connection

_SCHEMA_QUOTA = """CREATE TABLE IF NOT EXISTS daily_usage (
usage_date TEXT PRIMARY KEY,
used INTEGER NOT NULL
)"""

@dataclass
class DailyQuota:
"""Класс для работы с dailyquota."""
limit: int = settings.daily_email_limit
now_func: callable = field(
    default=lambda: datetime.now(timezone.utc)
    )  # injectable for tests
    _used: int = field(default=0, init=False)
    _date: date = field(default=None, init=False)

    def __post_init__(self):
    """Внутренний метод для post init."""
        if self._date is None:
        self._date = self.now_func().date()

    def load(self):
    """Выполняет load."""
    conn = get_connection()
    conn.execute(_SCHEMA_QUOTA)
    conn.commit()
    today = self._today_str()
    cur = conn.execute("SELECT used FROM daily_usage WHERE usage_date=?", (today,))
    row = cur.fetchone()
        if row:
        self._used = int(row[0])
    else:
        conn.execute(
            "INSERT OR IGNORE INTO daily_usage(usage_date, used) VALUES(?, 0)",
            (today,)
        )
        conn.commit()
    self._date = date.today()

    def _today_str(self) -> str:
    """Возвращает строковое представление сегодняшней даты.

    Returns:
        str: Дата в формате ISO (YYYY-MM-DD)
    """
        return self.now_func().date().isoformat()

    def _ensure_date(self):"""Внутренний метод для ensure date."

    Args:
    today = self.now_func().date()
        if today != self._date:
        self._date = today
        self._used = 0
        conn = get_connection()
        conn.execute("INSERT OR REPLACE INTO daily_usage(usage_date,used) VALUES(?,
            0)",(today.isoformat(),),"
        ")
        conn.commit()

    def can_send(self, count: int = 1) -> bool:"""выполняет can send."
    """Выполняет can send."""

    Args:
    count: Параметр для count

    Returns:
    bool: Результат выполнения операции"""
    self._ensure_date()
        return (self._used + count) <= self.limit

    def register(self, count: int = 1):"""выполняет register."
    """Выполняет register."""

    Args:
    count: Параметр для count"""
    self._ensure_date()
    self._used += count
    conn = get_connection()
    conn.execute("UPDATE daily_usage SET used=? WHERE usage_date=?",(self._used,
        self._today_str()),"
        ")
    conn.commit()

    def used(self) -> int:"""выполняет used."
    """Выполняет used."""

    Args:

    Returns:
    int: Результат выполнения операции"""
    self._ensure_date()
        return self._used

    def remaining(self) -> int:"""выполняет remaining."
    """Выполняет remaining."""

    Args:

    Returns:
    int: Результат выполнения операции"""
    self._ensure_date()
        return max(self.limit - self._used, 0)

    # --- Helpers for tests ---
    def current_day(self) -> str:"""выполняет current day."
    """Выполняет current day."""

    Args:

    Returns:
    str: Результат выполнения операции"""
        return self._date.isoformat()

    def reset("""выполняет reset."
    """Выполняет reset."""

    Args:
    day: Параметр для day"""
    self, day: Optional[date] = None
    ):  # pragma: no cover - primarily for tests
        if day is None:
        day = self.now_func().date()
    self._date = day
    self._used = 0
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO daily_usage(usage_date,used) VALUES(?,0)",
        (day.isoformat(),),"
        ")
    conn.commit()

__all__ = ["DailyQuota"]
