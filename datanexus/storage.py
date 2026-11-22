"""Transactional local development sink for raw and normalized events.

SQLite is intentionally a local reference sink, NOT a distributed lakehouse.
Insert is idempotent by event_id. Kafka offsets must be committed AFTER insert.
"""
import json
import sqlite3
from pathlib import Path
from datanexus.events import validate_envelope


class LocalEventStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS events (
          event_id TEXT PRIMARY KEY, source_time TEXT NOT NULL,
          tenant_id TEXT NOT NULL, icao24 TEXT NOT NULL,
          latitude REAL, longitude REAL, raw_json TEXT NOT NULL
        )""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_events_tenant_time ON events(tenant_id, source_time)")
        self.db.commit()

    def put(self, event):
        validate_envelope(event)
        payload = event["payload"]
        if not isinstance(payload.get("icao24"), str):
            raise ValueError("missing icao24")
        with self.db:
            cursor = self.db.execute(
                """INSERT OR IGNORE INTO events
                (event_id, source_time, tenant_id, icao24, latitude, longitude, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (event["event_id"], event["source_event_time"], event["tenant_id"],
                 payload["icao24"], payload.get("latitude"), payload.get("longitude"),
                 json.dumps(event, sort_keys=True)),
            )
        return cursor.rowcount == 1

    def count(self):
        return self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def close(self):
        self.db.close()
