from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import re

from .models import Item, aware_datetime


SYMBOLS = {"red": "🔴", "black": "⚫", "orange": "🟠", "blue": "🔵",
           "yellow": "🟡", "green": "🟢"}

DELIVERY_FAILURE = re.compile(
    r"(?:\bmail(?:er)?[ -]?daemon\b|\bpostmaster\b|\bundeliver(?:able|ed)\b|"
    r"\bdelivery (?:has )?failed\b|\bdelivery status notification \(failure\)|"
    r"\bfailure notice\b|\breturned mail\b)",
    re.IGNORECASE,
)
ROUTINE_FAILURE_WORDS = re.compile(
    r"\b(?:critical|error|failed|failure|unavailable|down|vulnerabilit(?:y|ies)|security alert)\b",
    re.IGNORECASE,
)
SUCCESSFUL_BACKUP = re.compile(
    r"\b(?:backup|job).{0,80}\b(?:completed successfully|successful|succeeded|success)\b|"
    r"\b(?:completed successfully|successful|succeeded|success).{0,80}\bbackup\b",
    re.IGNORECASE,
)
ROUTINE_SOURCE = re.compile(r"\b(?:github|logwatch)\b", re.IGNORECASE)


def apply_deterministic_safeguards(item: Item) -> Item:
    """Enforce narrow facts that must not depend on model interpretation."""
    if DELIVERY_FAILURE.search(f"{item.source} {item.summary}"):
        return replace(item, automated=True, exception=True)
    text = f"{item.source} {item.summary}"
    if SUCCESSFUL_BACKUP.search(text) or (
            ROUTINE_SOURCE.search(text) and not ROUTINE_FAILURE_WORDS.search(text)):
        return replace(item, automated=True, exception=False, service_impact=False,
                       blocked=False, action_required=False, waiting_for=False,
                       uncertain=False, ticket_recommended=False, ticket_reason=None)
    return item


def classify(item: Item, *, as_of: datetime) -> Item:
    item = apply_deterministic_safeguards(item)
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
    elif item.exception:
        flag, reason = "yellow", "automated_exception"
    else:
        flag, reason = "green", "information_only"
    durable_work = (item.service_impact or item.blocked or item.accumulating_issue
                    or item.overlooked or item.waiting_for or item.deadline is not None)
    if not (item.ticket_recommended and item.action_required and durable_work):
        item = replace(item, ticket_recommended=False, ticket_reason=None)
    return item.classified(flag=flag, symbol=SYMBOLS[flag], reason=reason)
