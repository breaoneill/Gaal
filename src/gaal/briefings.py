from __future__ import annotations

import hashlib
from collections.abc import Iterable

from .models import Item, Notification


SEVERITY = {"red": 0, "black": 1, "orange": 2, "blue": 3, "yellow": 4, "green": 5}


def reference(item: Item) -> str:
    """Stable non-reversible display reference; never expose provider message IDs."""
    digest = hashlib.sha256(item.id.encode("utf-8")).hexdigest()[:12]
    return f"olk:{digest}"


def daily(items: Iterable[Item]) -> Notification:
    ordered = sorted(items, key=lambda item: (SEVERITY[item.flag or "green"], item.id))
    title = "# Seldon daily briefing"
    if not ordered:
        body = f"{title}\n\nNo material activity.\n"
    else:
        lines = [title, ""] + [
            f"- {item.flag_symbol} {item.source}: {item.briefing_summary or item.summary} "
            f"{'🎫 ' if item.ticket_recommended else ''}[{reference(item)}]"
            for item in ordered
        ]
        body = "\n".join(lines) + "\n"
    return Notification(subject="Seldon daily briefing", body=body)
