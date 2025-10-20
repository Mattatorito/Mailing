from __future__ import annotations
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
    """Класс для работы с дневными лимитами email отправки."""
    limit: int = settings.daily_email_limit
    now_func: callable = field(
        default=lambda: datetime.now(timezone.utc)
    )  # injectable for tests
    _used: int = field(default=0, init=False)
    _date: date = field(default=None, init=False)

    def __post_init__(self):
        """Инициализация после создания объекта."""
        if self._date is None:
            self._date = self.now_func().date()

    def load(self):
        """Загружает текущее состояние из базы данных."""
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
        """Возвращает строковое представление сегодняшней даты."""
        return self.now_func().date().isoformat()

    def used(self) -> int:
        """Возвращает количество использованных отправок за день."""
        return self._used

    def remaining(self) -> int:
        """Возвращает количество оставшихся отправок."""
        return max(0, self.limit - self._used)

    def can_send(self, count: int = 1) -> bool:
        """Проверяет можно ли отправить указанное количество писем."""
        return self._used + count <= self.limit

    def register(self, count: int = 1) -> None:
        """Регистрирует отправку писем."""
        if not self.can_send(count):
            raise ValueError(f"Cannot send {count} emails, limit exceeded")
        
        self._used += count
        conn = get_connection()
        today = self._today_str()
        conn.execute(
            "UPDATE daily_usage SET used=? WHERE usage_date=?",
            (self._used, today)
        )
        conn.commit()

    def reset(self) -> None:
        """Сбрасывает счетчик на новый день."""
        today = self.now_func().date()
        if self._date != today:
            self._used = 0
            self._date = today