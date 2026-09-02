from __future__ import annotations

from datetime import date, datetime
from dataclasses import replace

from .briefings import daily
from .classification import classify
from .models import Notification
from .ports import Destination, ReasoningProvider, Source
from .schedule import WorkSchedule
from .store import SQLiteStore


class WorkflowFailure(RuntimeError):
    def __init__(self, stage: str):
        super().__init__(f"Gaal workflow failed during {stage}")
        self.stage = stage


class DuplicateDelivery(RuntimeError):
    pass


def run_daily(*, scheduled_date: date, actual_run_time: datetime,
              schedule: WorkSchedule, source: Source, destination: Destination,
              store: SQLiteStore, dry_run: bool = True,
              reasoning: ReasoningProvider | None = None) -> Notification:
    window = schedule.daily_window(scheduled_date)
    destination_name = getattr(destination, "name", type(destination).__name__)
    stage, status, failure, notification = "source_reading", "failed", None, None
    counts = {"fetched": 0, "interpreted": 0, "classified": 0,
              "rendered": 0, "delivered": 0}
    try:
        if not dry_run and store.was_delivered(
                workflow_name="daily_briefing", scheduled_time=window.end.isoformat(),
                destination=destination_name):
            stage = "idempotency"
            raise DuplicateDelivery("briefing was already delivered for this scheduled window")
        items = source.read(window.start, window.end)
        counts["fetched"] = len(items)
        if reasoning is not None:
            stage = "reasoning"
            items = reasoning.interpret(items)
        counts["interpreted"] = len(items)
        stage = "history"
        items = [replace(item, overlooked=True)
                 if item.action_required
                 and (history := store.item_history(item)) is not None
                 and history["last_flag"] in {"green", "yellow"}
                 else item for item in items]
        stage = "classification"
        classified = [classify(item, as_of=actual_run_time) for item in items]
        counts["classified"] = len(classified)
        store.record_items(classified, observed_at=actual_run_time.isoformat())
        stage = "rendering"
        notification = daily(classified, window=window, reviewed_count=counts["fetched"])
        counts["rendered"] = len(classified)
        stage = "destination_dispatch"
        destination.deliver(notification, dry_run=dry_run)
        counts["delivered"] = len(classified)
        status = "dry_run" if dry_run else "delivered"
    except Exception as exc:
        failure = exc
    record = {
        "workflow_name": "daily_briefing",
        "scheduled_time": window.end.isoformat(),
        "actual_run_time": actual_run_time.isoformat(),
        "timezone": schedule.timezone,
        "input_window": {"start": window.start.isoformat(), "end": window.end.isoformat()},
        "output_destination": destination_name,
        "delivery_status": status,
        "dry_run": dry_run,
        "failure_stage": stage if failure else None,
        "counts": counts,
    }
    try:
        store.append_run(record)
    except Exception as exc:
        raise WorkflowFailure("audit") from exc
    if failure:
        raise WorkflowFailure(stage) from failure
    assert notification is not None
    return notification
