from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from .models import Item, Notification


class Source(Protocol):
    def read(self, start: datetime, end: datetime) -> Sequence[Item]: ...


class Destination(Protocol):
    def deliver(self, notification: Notification, *, dry_run: bool) -> None: ...


class ReasoningProvider(Protocol):
    """Extracts facts; deterministic Gaal policy remains authoritative."""

    def interpret(self, items: Sequence[Item]) -> Sequence[Item]: ...


class CalendarProvider(Protocol):
    """Future availability overrides; static WorkSchedule is authoritative today."""


class TelegramDestination(Destination, Protocol):
    """Future Telegram delivery boundary."""


class EmailDestination(Destination, Protocol):
    """Future Microsoft 365 email delivery boundary."""


class ZammadDestination(Protocol):
    """Future approval-gated durable ticket boundary."""

    def create_ticket(self, subject: str, body: str, *, dry_run: bool) -> None: ...
