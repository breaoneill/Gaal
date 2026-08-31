from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import Item, Notification


class JsonFileSource:
    """Read normalized fixture data; no mailbox mutation is possible."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def read(self, start: datetime, end: datetime) -> list[Item]:
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise ValueError("source input must be a JSON list")
        items = [Item.from_dict(item) for item in value]
        return [item for item in items if start <= item.occurred_at < end]


class StdoutDestination:
    name = "stdout:daily-briefing"
    def __init__(self, write):
        self.write = write

    def deliver(self, notification: Notification, *, dry_run: bool) -> None:
        if not dry_run:
            raise RuntimeError("stdout destination is available only in dry-run mode")
        self.write(notification.body)
