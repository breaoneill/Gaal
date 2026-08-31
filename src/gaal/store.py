from __future__ import annotations

import json
import sqlite3
import hashlib
from contextlib import closing
from pathlib import Path


class SQLiteStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_runs (
                        id INTEGER PRIMARY KEY,
                        workflow_name TEXT NOT NULL,
                        scheduled_time TEXT NOT NULL,
                        actual_run_time TEXT NOT NULL,
                        input_start TEXT NOT NULL,
                        input_end TEXT NOT NULL,
                        destination TEXT NOT NULL,
                        delivery_status TEXT NOT NULL,
                        dry_run INTEGER NOT NULL,
                        failure_stage TEXT,
                        metadata_json TEXT NOT NULL
                    )
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS item_state (
                        tracking_key TEXT PRIMARY KEY,
                        first_seen TEXT NOT NULL,
                        last_seen TEXT NOT NULL,
                        seen_count INTEGER NOT NULL,
                        last_status TEXT NOT NULL,
                        last_flag TEXT NOT NULL,
                        last_reason TEXT NOT NULL
                    )
                """)
                columns = {row[1] for row in connection.execute("PRAGMA table_info(item_state)")}
                if "last_ticket_recommended" not in columns:
                    connection.execute(
                        "ALTER TABLE item_state ADD COLUMN last_ticket_recommended INTEGER NOT NULL DEFAULT 0"
                    )

    @staticmethod
    def tracking_key(item) -> str:
        value = item.thread_id or item.id
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def item_history(self, item) -> dict[str, object] | None:
        self.initialize()
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute(
                """SELECT first_seen, last_seen, seen_count, last_status, last_flag, last_reason,
                          last_ticket_recommended
                   FROM item_state WHERE tracking_key = ?""",
                (self.tracking_key(item),),
            ).fetchone()
        if not row:
            return None
        return dict(zip(("first_seen", "last_seen", "seen_count", "last_status",
                         "last_flag", "last_reason", "last_ticket_recommended"), row))

    def record_items(self, items, *, observed_at: str) -> None:
        self.initialize()
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                for item in items:
                    connection.execute(
                        """INSERT INTO item_state (
                            tracking_key, first_seen, last_seen, seen_count,
                            last_status, last_flag, last_reason, last_ticket_recommended
                        ) VALUES (?, ?, ?, 1, ?, ?, ?, ?)
                        ON CONFLICT(tracking_key) DO UPDATE SET
                            last_seen = excluded.last_seen,
                            seen_count = item_state.seen_count + 1,
                            last_status = excluded.last_status,
                            last_flag = excluded.last_flag,
                            last_reason = excluded.last_reason,
                            last_ticket_recommended = excluded.last_ticket_recommended""",
                        (self.tracking_key(item), observed_at, observed_at, item.status,
                         item.flag, item.reason, int(item.ticket_recommended)),
                    )

    def was_delivered(self, *, workflow_name: str, scheduled_time: str,
                      destination: str) -> bool:
        self.initialize()
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute(
                """SELECT 1 FROM workflow_runs
                   WHERE workflow_name = ? AND scheduled_time = ? AND destination = ?
                     AND delivery_status = 'delivered'
                   LIMIT 1""",
                (workflow_name, scheduled_time, destination),
            ).fetchone()
        return row is not None

    def append_run(self, record: dict[str, object]) -> None:
        self.initialize()
        window = record["input_window"]
        assert isinstance(window, dict)
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                connection.execute(
                    """INSERT INTO workflow_runs (
                        workflow_name, scheduled_time, actual_run_time, input_start,
                        input_end, destination, delivery_status, dry_run,
                        failure_stage, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (record["workflow_name"], record["scheduled_time"], record["actual_run_time"],
                     window["start"], window["end"], record["output_destination"],
                     record["delivery_status"], int(bool(record["dry_run"])),
                     record["failure_stage"], json.dumps(record, sort_keys=True)),
                )

    def last_run(self) -> dict[str, object] | None:
        self.initialize()
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute(
                "SELECT metadata_json FROM workflow_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return json.loads(row[0]) if row else None
