from __future__ import annotations

from datetime import datetime

from .models import Item, aware_datetime


SYMBOLS = {"red": "🔴", "black": "⚫", "orange": "🟠", "blue": "🔵",
           "yellow": "🟡", "green": "🟢"}


def classify(item: Item, *, as_of: datetime) -> Item:
    now = aware_datetime(as_of, "as_of")
    if item.service_impact:
        flag, reason = "red", "service_impact"
    elif item.blocked:
        flag, reason = "red", "blocked"
    elif item.action_required and item.deadline is not None and item.deadline <= now:
        flag, reason = "red", "deadline_due"
    elif item.accumulating_issue:
        flag, reason = "black", "accumulating_issue"
    elif item.overlooked:
        flag, reason = "blue", "overlooked"
    elif item.action_required:
        flag, reason = "orange", "action_required"
    elif item.automated and not item.exception:
        flag, reason = "green", "routine_automation"
    elif item.waiting_for:
        flag, reason = "yellow", "waiting_for"
    elif item.uncertain:
        flag, reason = "yellow", "uncertain"
    else:
        flag, reason = "green", "information_only"
    return item.classified(flag=flag, symbol=SYMBOLS[flag], reason=reason)
