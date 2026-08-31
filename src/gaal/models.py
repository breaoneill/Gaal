from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime


BOOLEAN_FIELDS = (
    "accumulating_issue", "action_required", "automated", "blocked", "exception",
    "overlooked", "service_impact", "uncertain", "waiting_for",
)
STATUSES = {"open", "resolved", "waiting"}


def aware_datetime(value: str | datetime, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value) if isinstance(value, str) else value
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a UTC offset")
    return parsed


@dataclass(frozen=True)
class Item:
    id: str
    occurred_at: datetime
    source: str
    summary: str
    status: str
    thread_id: str | None = None
    deadline: datetime | None = None
    service_impact: bool = False
    blocked: bool = False
    action_required: bool = False
    waiting_for: bool = False
    uncertain: bool = False
    automated: bool = False
    exception: bool = False
    accumulating_issue: bool = False
    overlooked: bool = False
    evidence: tuple[str, ...] = ()
    briefing_summary: str | None = None
    ticket_recommended: bool = False
    ticket_reason: str | None = None
    flag: str | None = None
    flag_symbol: str | None = None
    reason: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "Item":
        allowed = {field.name for field in cls.__dataclass_fields__.values()} - {
            "flag", "flag_symbol", "reason"
        }
        missing = {"id", "occurred_at", "source", "summary", "status"} - value.keys()
        unknown = value.keys() - allowed
        if missing:
            raise ValueError(f"normalized item missing fields: {', '.join(sorted(missing))}")
        if unknown:
            raise ValueError(f"normalized item has unknown fields: {', '.join(sorted(unknown))}")
        for field in ("id", "source", "summary"):
            if not isinstance(value[field], str) or not value[field].strip():
                raise ValueError(f"normalized item {field} must be a non-empty string")
        if value["status"] not in STATUSES:
            raise ValueError(f"invalid normalized item status: {value['status']}")
        for field in BOOLEAN_FIELDS:
            if field in value and not isinstance(value[field], bool):
                raise ValueError(f"{field} must be a boolean")
        data = dict(value)
        evidence = data.get("evidence", ())
        if not isinstance(evidence, (list, tuple)) or any(
                not isinstance(entry, str) or not entry.strip() for entry in evidence):
            raise ValueError("evidence must be a list of non-empty strings")
        data["evidence"] = tuple(evidence)
        briefing_summary = data.get("briefing_summary")
        if briefing_summary is not None and (
                not isinstance(briefing_summary, str) or not briefing_summary.strip()):
            raise ValueError("briefing_summary must be a non-empty string")
        ticket_recommended = data.get("ticket_recommended", False)
        ticket_reason = data.get("ticket_reason")
        if not isinstance(ticket_recommended, bool):
            raise ValueError("ticket_recommended must be a boolean")
        if ticket_recommended and (
                not isinstance(ticket_reason, str) or not ticket_reason.strip()):
            raise ValueError("ticket_reason is required when a ticket is recommended")
        if not ticket_recommended and ticket_reason is not None:
            raise ValueError("ticket_reason requires ticket_recommended")
        data["occurred_at"] = aware_datetime(value["occurred_at"], "occurred_at")
        if value.get("deadline") is not None:
            data["deadline"] = aware_datetime(value["deadline"], "deadline")
        return cls(**data)

    def classified(self, *, flag: str, symbol: str, reason: str) -> "Item":
        return replace(self, flag=flag, flag_symbol=symbol, reason=reason)


@dataclass(frozen=True)
class Window:
    start: datetime
    end: datetime


@dataclass(frozen=True)
class Notification:
    subject: str
    body: str
    priority: str = "normal"
