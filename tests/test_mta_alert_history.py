"""Phase 3.8 local append-only history and protected reader tests; no Kafka."""
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
for d in ("scripts","apps/api"):sys.path.insert(0,str(ROOT/d))
def load(path,name):
 s=importlib.util.spec_from_file_location(name,ROOT/path)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
writer=load("scripts/register_mta_alert.py","register_mta_alert")
reader=load("apps/api/mta_alert_history.py","mta_alert_history")
NOW=datetime(2026,11,27,12,tzinfo=timezone.utc)

def sample():
 stamp=NOW-timedelta(seconds=20)
 provider=stamp-timedelta(seconds=600)
 return {"state":"local_monitor_snapshot","checked_at_utc":stamp.isoformat(),
 "latest_provider_timestamp_utc":provider.isoformat(),
 "latest_stored_source_age_seconds":600,"topic":"mta.subway.updates.v1",
 "group":"datanexus-mta-aggregate-v1","production_approved":False,
 "source_api_checked_now":False,"offset_state":"valid","low_offset":0,
 "high_offset_exclusive":6,"committed_next_offset":6,"consumer_lag_messages":0}
class HistoryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.source=self.root/"monitor.json"
  self.source.write_text(json.dumps(sample()),encoding="utf-8")
  self.folder=self.root/"mta"/"alert_history"
 def test_records_warning_and_is_idempotent(self):
  path,entry,created=writer.register_snapshot(self.source,self.folder,now=NOW)
  self.assertTrue(created)
  self.assertEqual(entry["alert_count"],1)
  self.assertEqual(entry["incident_lifecycle"],"unreviewed")
  again,entry2,created2=writer.register_snapshot(self.source,self.folder,now=NOW)
  self.assertEqual(path,again);self.assertFalse(created2)
  self.assertEqual(entry2["assessed_at_utc"],entry["assessed_at_utc"])
 def test_bounded_authenticated_reader_contract(self):
  writer.register_snapshot(self.source,self.folder,now=NOW)
  result=reader.read_alert_history(self.root)
  self.assertEqual(result["count"],1)
  self.assertEqual(result["entries"][0]["alerts"][0]["code"],"STORED_OBSERVATION_OLD")
  self.assertFalse(result["production_approved"])
 def test_missing_history_does_not_claim_health(self):
  result=reader.read_alert_history(self.root)
  self.assertEqual(result["count"],0)
  self.assertIn("not a clean bill",result["caveat"])
 def test_tampered_entry_fails_closed(self):
  path,_,_=writer.register_snapshot(self.source,self.folder,now=NOW)
  bad=json.loads(path.read_text())
  bad["incident_lifecycle"]="resolved"
  path.write_text(json.dumps(bad))
  with self.assertRaises(ValueError):reader.read_alert_history(self.root)
 def test_bad_source_fails_closed(self):
  d=sample();d["consumer_lag_messages"]=9
  self.source.write_text(json.dumps(d))
  with self.assertRaises(ValueError):writer.register_snapshot(self.source,self.folder,now=NOW)
 def test_protected_endpoint_and_pipeline_isolation(self):
  main=(ROOT/"apps/api/main.py").read_text()
  proxy=(ROOT/"apps/web/app/api/portal/[...path]/route.ts").read_text()
  self.assertIn('"/api/v1/mta/alert-history"',main)
  self.assertIn('require_permission("quality:read")',main)
  self.assertIn('"mta/alert-history"',proxy)
  self.assertNotIn("aviation.states.v1",(ROOT/"scripts/register_mta_alert.py").read_text())
