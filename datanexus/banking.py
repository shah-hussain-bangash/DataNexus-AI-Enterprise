"""Local event projection for synthetic Workbench credit events."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from uuid import UUID

from datanexus.events import validate_envelope


def ingest_credit_feed(path, fetch, *, max_pages=100):
    """Commit each page with its cursor and keep replays idempotent."""
    if max_pages < 1:
        raise ValueError("At least one page is required")
    with closing(sqlite3.connect(path, timeout=10)) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS banking_cursor (source TEXT PRIMARY KEY, position INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS banking_events (
                id TEXT PRIMARY KEY, source TEXT NOT NULL, case_id TEXT NOT NULL,
                booked_amount INTEGER, envelope TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS banking_one_booking
                ON banking_events(source, case_id) WHERE booked_amount IS NOT NULL;
        """)
        source = None
        position = 0
        added = 0
        for _ in range(max_pages):
            page = fetch(position)
            page_source = str(UUID(page["source_id"]))
            if source is None:
                source = page_source
                saved = db.execute("SELECT position FROM banking_cursor WHERE source = ?", (source,)).fetchone()
                if saved and saved[0] > position:
                    position = saved[0]
                    page = fetch(position)
            if str(UUID(page["source_id"])) != source:
                raise ValueError("Workbench source changed during the ingest")
            if type(page["has_more"]) is not bool or type(page["next_after"]) is not int:
                raise ValueError("Invalid Workbench page metadata")
            with db:
                db.execute("BEGIN IMMEDIATE")
                for event in page["events"]:
                    position_next = event["sequence"]
                    if (type(position_next) is not int or position_next <= position
                            or type(event["schema_version"]) is not int or event["schema_version"] != 1
                            or event["event_id"] != f"banking-demo:{position_next}"):
                        raise ValueError("Invalid Workbench event sequence")
                    position = position_next
                    case_id = str(UUID(event["case_id"]))
                    event_id = f"{source}:{event['event_id']}"
                    amount = event.get("booked_amount_aed")
                    if event["event_type"] == "booking_reconciled":
                        if type(amount) is not int or not 0 < amount <= 10**12:
                            raise ValueError("Invalid Workbench booking amount")
                    elif amount is not None:
                        raise ValueError("Unexpected booking amount")
                    envelope = validate_envelope({
                        "event_id": event_id, "source": "uae-banking.workbench", "schema_version": "1.0",
                        "source_event_time": event["occurred_at"], "ingested_at": datetime.now(timezone.utc).isoformat(),
                        "tenant_id": "synthetic-" + source, "trace_id": case_id, "payload": event,
                    })
                    serialized = json.dumps(envelope, sort_keys=True)
                    result = db.execute(
                        "INSERT INTO banking_events VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
                        (event_id, source, case_id, amount, serialized),
                    )
                    if result.rowcount == 0:
                        original = db.execute("SELECT envelope FROM banking_events WHERE id = ?", (event_id,)).fetchone()
                        stored = json.loads(original[0])
                        if stored["payload"] != event:
                            raise ValueError("Conflicting Workbench event replay")
                    added += result.rowcount
                if page["next_after"] != position or (page["has_more"] and not page["events"]):
                    raise ValueError("Invalid Workbench event cursor")
                db.execute(
                    "INSERT INTO banking_cursor VALUES (?, ?) ON CONFLICT(source) DO UPDATE "
                    "SET position = MAX(position, excluded.position)", (source, position),
                )
            if not page["has_more"]:
                break
        count, exposure = db.execute(
            "SELECT COUNT(booked_amount), COALESCE(SUM(booked_amount), 0) FROM banking_events WHERE source = ?",
            (source,),
        ).fetchone()
        return {"new_events": added, "booked_facilities": count, "booked_exposure_aed": exposure,
                "cursor": position, "has_more": page["has_more"]}
