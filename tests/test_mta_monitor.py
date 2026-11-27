"""Phase 3.6 Kafka monitor unit tests. Broker-free, no MTA API requests."""
import importlib.util
import json
import sys
import tempfile
import sqlite3
import unittest
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for dir in ("scripts","apps/api"):sys.path.insert(0,str(ROOT/dir))
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,ROOT/path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
m=load("scripts/monitor_mta.py","mta_monitor")
api=load("apps/api/mta_monitor.py","mta_monitor_api")
NOW=datetime(2026,11,27,12,tzinfo=timezone.utc)
class Partition:
 def __init__(self,topic,partition):self.topic=topic;self.partition=partition
class Broker:
 offset=6;low=0;high=6
 def __init__(self,config):self.config=config
 def list_topics(self,topic,timeout):
  return type("M",(),{"topics":{m.TOPIC:type("T",(),{"error":None,"partitions":{0:object()}})()}})()
 def get_watermark_offsets(self,tp,timeout,cached):return self.low,self.high
 def committed(self,tps,timeout):return [type("O",(),{"offset":self.offset})()]
 def close(self):pass
class MonitorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/"mta"/"mta_aggregate.sqlite3"
  self.path.parent.mkdir()
  with closing(sqlite3.connect(self.path)) as db:
   with db:
    db.execute("CREATE TABLE mta_aggregates (provider_timestamp_utc TEXT)")
    db.execute("INSERT INTO mta_aggregates VALUES (?)",("2026-11-27T11:59:00+00:00",))
 def run_check(self,broker=Broker):
  return m.snapshot(db_path=self.path,consumer_factory=broker,partition_factory=Partition,clock=NOW)
 def test_valid_lag_and_stored_freshness(self):
  result=self.run_check()
  self.assertEqual(result["consumer_lag_messages"],0)
  self.assertEqual(result["latest_stored_source_age_seconds"],60)
  self.assertFalse(result["source_api_checked_now"])
 def test_uncommitted_lag_is_unknown_not_zero(self):
  class Missing(Broker):offset=-1001
  r=self.run_check(Missing)
  self.assertIsNone(r["consumer_lag_messages"])
  self.assertEqual(r["offset_state"],"unknown_uncommitted")
 def test_lag_and_offset_before_retention(self):
  class Backlog(Broker):offset=3;low=2;high=6
  self.assertEqual(self.run_check(Backlog)["consumer_lag_messages"],3)
  class Expired(Broker):offset=1;low=2;high=6
  self.assertEqual(self.run_check(Expired)["offset_state"],"committed_below_retention")
 def test_saved_snapshot_is_explicit_and_staleness_measured(self):
  report=self.run_check()
  folder=Path(self.tmp.name)/"mta"/"monitor_checks"
  path=m.save_new(report,folder)
  self.assertTrue(path.is_file())
  with self.assertRaises(FileExistsError):m.save_new(report,folder)
  value=api.latest_monitor(self.tmp.name,now=NOW)
  self.assertFalse(value["snapshot_stale"])
  future=datetime(2026,11,27,12,10,tzinfo=timezone.utc)
  self.assertTrue(api.latest_monitor(self.tmp.name,now=future)["snapshot_stale"])
 def test_protected_endpoint_and_no_aviation_modifications(self):
  main=(ROOT/"apps/api/main.py").read_text()
  proxy=(ROOT/"apps/web/app/api/portal/[...path]/route.ts").read_text()
  self.assertIn('"/api/v1/mta/monitor"',main)
  self.assertIn('require_permission("quality:read")',main)
  self.assertIn('"mta/monitor"',proxy)
  self.assertNotIn("aviation.states.v1",(ROOT/"scripts/monitor_mta.py").read_text())
