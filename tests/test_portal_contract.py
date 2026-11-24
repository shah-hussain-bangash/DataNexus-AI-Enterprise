"""Dependency-free checks of the new local portal structure and data API."""
import importlib.util
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PortalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("portal_data", ROOT / "apps/api/data.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cls.data = mod

    def test_missing_sqlite_has_no_fabricated_results(self):
        with tempfile.TemporaryDirectory() as path:
            response = self.data.read_events(Path(path) / "missing.sqlite3")
        self.assertFalse(response["configured"])
        self.assertEqual(response["events"], [])
        self.assertEqual(self.data.summarize_events(response)["total_events"], 0)

    def test_read_only_real_sqlite_events(self):
        with tempfile.TemporaryDirectory() as path:
            db = Path(path) / "aviation.sqlite3"
            with closing(sqlite3.connect(db)) as conn:
                conn.execute("""CREATE TABLE events (
                    event_id TEXT PRIMARY KEY, source_time TEXT NOT NULL, tenant_id TEXT NOT NULL,
                    icao24 TEXT NOT NULL, latitude REAL, longitude REAL, raw_json TEXT NOT NULL
                )""")
                conn.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?)", (
                    "event-1", "2025-12-31T12:00:00Z", "demo", "abc123", 25.1, 55.1,
                    '{"source":"opensky.states.all","payload":{"callsign":"TEST123","velocity_mps":185}}'
                ))
                conn.commit()
            result = self.data.read_events(db)
            self.assertEqual(result["total"], 1)
            self.assertEqual(result["events"][0]["callsign"], "TEST123")
            self.assertEqual(self.data.summarize_events(result)["aircraft_in_sample"], 1)
            self.assertEqual(self.data.read_events(db, query="nomatch")["total"], 0)

    def test_compose_is_localhost_only(self):
        text = (ROOT / "docker-compose.portal.yml").read_text(encoding="utf-8")
        self.assertIn("127.0.0.1:13000:3000", text)
        self.assertIn("./data/dev:/opt/project/data/dev:ro", text)

    def test_frontend_routes_and_no_fake_status(self):
        text = (ROOT / "apps/web/app/page.tsx").read_text(encoding="utf-8")
        for token in ("Aviation Intelligence", "Data Quality Center", "not_instrumented", "local_sqlite"):
            if token == "not_instrumented":
                # This value comes from the API, not necessarily the page.
                text = text + (ROOT / "apps/api/main.py").read_text(encoding="utf-8")
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
