"""Phase 3.4 MTA bounded read-only API and dashboard contracts."""
import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"apps/api"))
s=importlib.util.spec_from_file_location("mta_observations",ROOT/"apps/api/mta_observations.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class MTAReadTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.path=Path(self.temp.name)/"mta"/"mta_aggregate.sqlite3"
 def build(self):
  self.path.parent.mkdir()
  with sqlite3.connect(self.path) as db:
   db.execute("""CREATE TABLE mta_aggregates (
    event_id TEXT PRIMARY KEY, provider_timestamp_utc TEXT NOT NULL, observed_at_utc TEXT NOT NULL,
    feed_id TEXT NOT NULL,response_sha256 TEXT NOT NULL,entities INTEGER NOT NULL,
    trip_updates INTEGER NOT NULL,vehicle_positions INTEGER NOT NULL,alerts INTEGER NOT NULL)""")
   db.execute("INSERT INTO mta_aggregates VALUES (?,?,?,?,?,?,?,?,?)",
    ("a"*64,"2026-11-26T11:55:41+00:00","2026-11-26T11:55:43+00:00","ace","b"*64,124,62,62,0))
 def test_missing_source_does_not_fabricate(self):
  with self.assertRaises(FileNotFoundError):m.read_mta_observations(self.temp.name)
 def test_verified_local_observations_bounded(self):
  self.build()
  result=m.read_mta_observations(self.temp.name)
  self.assertEqual(result["count"],1)
  self.assertEqual(result["observations"][0]["entities"],124)
  self.assertFalse(result["live_stream_connected"])
  self.assertFalse(result["production_approved"])
  with self.assertRaises(ValueError):m.read_mta_observations(self.temp.name,51)
 def test_invalid_stored_record_fails_closed(self):
  self.build()
  with sqlite3.connect(self.path) as db:db.execute("UPDATE mta_aggregates SET entities=-5")
  with self.assertRaises(ValueError):m.read_mta_observations(self.temp.name)
 def test_protected_routes_are_wired(self):
  self.assertIn('require_permission("quality:read")',(ROOT/"apps/api/main.py").read_text())
  self.assertIn('"/api/v1/mta/observations"',(ROOT/"apps/api/main.py").read_text())
  self.assertIn('"mta/observations"',(ROOT/"apps/web/app/api/portal/[...path]/route.ts").read_text())
  self.assertIn('load<MtaResponse>("mta/observations",setMta)',(ROOT/"apps/web/app/workspaces/backend-evidence.tsx").read_text())
  self.assertIn("mta_observations.py",(ROOT/"apps/api/Dockerfile").read_text())
