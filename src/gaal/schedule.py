from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .models import Window


DAY_NUMBERS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


@dataclass(frozen=True)
class WorkSchedule:
    timezone: str
    days: tuple[str, ...]
    start: time
    finish: time

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    def daily_window(self, scheduled_date: date) -> Window:
        allowed = {DAY_NUMBERS[day] for day in self.days}
        if scheduled_date.weekday() not in allowed:
            raise ValueError(f"daily briefing is not scheduled on {scheduled_date.isoformat()}")
        previous = scheduled_date - timedelta(days=1)
        while previous.weekday() not in allowed:
            previous -= timedelta(days=1)
        return Window(
            start=datetime.combine(previous, self.finish, tzinfo=self.zone),
            end=datetime.combine(scheduled_date, self.start, tzinfo=self.zone),
        )
