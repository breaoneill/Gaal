from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from .models import Item, Notification, Window


SEVERITY = {"red": 0, "black": 1, "orange": 2, "blue": 3, "yellow": 4, "green": 5}
MAX_PRIORITIES = 5
BACKUP_FAILURE = re.compile(
    r"\bbackup\b.*\b(?:fail(?:ed|ure)?|could not|unable|error|warning)\b|"
    r"\b(?:fail(?:ed|ure)?|could not|unable|error|warning)\b.*\bbackup\b",
    re.IGNORECASE,
)
BACKUP_KINDS = (
    (re.compile(r"\b(?:rdx|cartridge)\b", re.IGNORECASE), "RDX/cartridge"),
    (re.compile(r"\bverif(?:y|ication)\b", re.IGNORECASE), "verification"),
    (re.compile(r"\bduplicity\b", re.IGNORECASE), "duplicity"),
    (re.compile(r"\bcron\b", re.IGNORECASE), "cron"),
    (re.compile(r"\b(?:backup share|share could not be mounted)\b", re.IGNORECASE),
     "backup-share"),
)


def reference(item: Item) -> str:
    """Retained for audit/debug tooling; daily briefings do not expose item IDs."""
    digest = hashlib.sha256(item.id.encode("utf-8")).hexdigest()[:12]
    return f"olk:{digest}"


def _window(window: Window | None) -> str | None:
    if window is None:
        return None
    start = window.start.strftime("%a %-d %b %H:%M")
    end = window.end.strftime("%a %-d %b %H:%M %Z")
    return f"Window reviewed: {start} to {end}."


def _group(items: list[Item]) -> tuple[list[str], int]:
    backup = [item for item in items if BACKUP_FAILURE.search(item.summary)]
    backup_ids = {item.id for item in backup}
    priorities: list[tuple[int, str]] = []
    consolidated = 0
    if backup:
        kinds = [label for pattern, label in BACKUP_KINDS
                 if any(pattern.search(item.summary) for item in backup)]
        detail = f", including {', '.join(kinds)} issues" if kinds else ""
        priorities.append((min(SEVERITY[item.flag or "green"] for item in backup),
                           f"Backup failures: {len(backup)} alerts{detail} need triage."))
        consolidated += len(backup) - 1

    threads: dict[str, list[Item]] = {}
    for item in items:
        if item.id not in backup_ids:
            threads.setdefault(item.thread_id or item.id, []).append(item)
    for related in threads.values():
        chosen = sorted(related, key=lambda item: (
            SEVERITY[item.flag or "green"], -item.occurred_at.timestamp()))[0]
        priorities.append((SEVERITY[chosen.flag or "green"],
                           f"{chosen.source}: {chosen.briefing_summary or chosen.summary}"))
        consolidated += len(related) - 1
    priorities.sort(key=lambda value: value[0])
    hidden = max(0, len(priorities) - MAX_PRIORITIES)
    return [text for _, text in priorities[:MAX_PRIORITIES]], consolidated + hidden


def _summary(priorities: list[str], *, omitted: int, consolidated: int) -> str:
    labels = [priority.split(":", 1)[0] for priority in priorities]
    if not labels:
        return "No material activity needs attention this morning."
    subjects = labels[0] if len(labels) == 1 \
        else f"{', '.join(labels[:-1])}, and {labels[-1]}"
    context = []
    if omitted:
        context.append(f"{omitted} routine or informational messages omitted")
    if consolidated:
        context.append(f"{consolidated} related or lower-priority items consolidated")
    suffix = f" {'; '.join(context).capitalize()}." if context else ""
    return f"Main things needing attention today: {subjects}.{suffix}"


def daily(items: Iterable[Item], *, window: Window | None = None,
          reviewed_count: int | None = None) -> Notification:
    values = list(items)
    material = [item for item in values if item.flag != "green"]
    priorities, consolidated = _group(material)
    omitted = len(values) - len(material)
    lines = ["Morning Email Briefing"]
    if (description := _window(window)) is not None:
        lines.extend(["", description])
    if reviewed_count is not None:
        lines.append(f"I reviewed {reviewed_count} messages. I did not modify any email.")
    lines.extend(["", "1. Executive Summary", "",
                  _summary(priorities, omitted=omitted, consolidated=consolidated)])
    if priorities:
        lines.extend(["", "2. Today's Priorities", ""])
        lines.extend(f"{index}. {priority}" for index, priority in enumerate(priorities, 1))
    return Notification(subject="Morning Email Briefing", body="\n".join(lines) + "\n")
