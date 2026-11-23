import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from datanexus.events import normalize_states
from datanexus.lakehouse import export_layers
from datanexus.storage import LocalEventStore


FIXTURE = Path(__file__).parent / "fixtures" / "opensky-states.json"


class LakehouseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "events.sqlite3"
        self.target = Path(self.tmp.name) / "lakehouse"
        source = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.events = normalize_states(source, collected_at="2026-01-01T00:00:00Z")
        with_store = LocalEventStore(self.db)
        for event in self.events:
            with_store.put(event)
        with_store.close()

    def test_medallion_export(self):
        metrics = export_layers(self.db, self.target)
        self.assertEqual(metrics["bronze_records"], 2)
        self.assertEqual(metrics["silver_records"], 2)
        self.assertEqual(metrics["quarantined_records"], 0)
        gold = json.loads((self.target / "gold/daily_aircraft_summary.jsonl").read_text().strip())
        self.assertEqual(gold["event_count"], 2)
        self.assertEqual(gold["distinct_aircraft"], 2)

    def test_reproducible_export(self):
        export_layers(self.db, self.target)
        first = (self.target / "silver/aviation_states.jsonl").read_bytes()
        export_layers(self.db, self.target)
        self.assertEqual(first, (self.target / "silver/aviation_states.jsonl").read_bytes())

    def test_invalid_coordinates_quarantined(self):
        bad = dict(self.events[0])
        bad["event_id"] = "invalid-test-id"
        bad["payload"] = dict(bad["payload"], latitude=999.0)
        with sqlite3.connect(self.db) as db:
            db.execute(
                "INSERT INTO events (event_id, source_time, tenant_id, icao24, latitude, longitude, raw_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (bad["event_id"], bad["source_event_time"], bad["tenant_id"], bad["payload"]["icao24"],
                 999.0, 55.2, json.dumps(bad)),
            )
        metrics = export_layers(self.db, self.target)
        self.assertEqual(metrics["bronze_records"], 3)
        self.assertEqual(metrics["silver_records"], 2)
        self.assertEqual(metrics["quarantined_records"], 1)
        reasons = (self.target / "quarantine/invalid_records.jsonl").read_text()
        self.assertIn("invalid_coordinates", reasons)

    def test_missing_input_fails(self):
        with self.assertRaises(FileNotFoundError):
            export_layers(Path(self.tmp.name) / "missing.db", self.target)


if __name__ == "__main__":
    unittest.main()
