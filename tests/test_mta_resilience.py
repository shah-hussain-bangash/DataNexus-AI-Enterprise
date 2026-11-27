"""Phase 3.10: broker/SQLite failure injection and isolated restore; no live Kafka."""
import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
def load(path,name):
 s=importlib.util.spec_from_file_location(name,ROOT/path)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=load("scripts/consume_mta_aggregate.py","mta_resilience_consumer")
b=load("scripts/backup_verify_mta.py","mta_resilience_backup")
def event():
 return {"event_id":"a"*64,"schema_version":"1.0","source":"mta_nyct_subway_gtfs_rt",
 "feed_id":"ace","provider_timestamp_utc":"2026-11-27T07:20:23+00:00",
 "observed_at_utc":"2026-11-27T07:20:24+00:00","provider_response_sha256":"b"*64,
 "counts":{"entities":100,"trip_updates":50,"vehicle_positions":50,"alerts":0},
 "kind":"one_shot_aggregate","production_approved":False}
class Message:
 def __init__(self,data=None,error=None):self.data=data;self.failure=error
 def value(self):return json.dumps(self.data).encode()
 def key(self):return self.data["event_id"].encode()
 def topic(self):return c.TOPIC
 def partition(self):return 0
 def offset(self):return 0
 def error(self):return self.failure
class Broker:
 next_message=None
 fail_subscribe=False
 fail_commit=False
 commits=0
 def __init__(self,config):self.config=config
 def subscribe(self,topics):
  if self.fail_subscribe:raise RuntimeError("simulated broker connection refused")
 def poll(self,timeout):return self.next_message
 def commit(self,**kwargs):
  if self.fail_commit:raise RuntimeError("simulated commit timeout")
  type(self).commits+=1
 def close(self):pass
class ResilienceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.db=self.root/"mta.sqlite3"
  Broker.next_message=None;Broker.fail_subscribe=False;Broker.fail_commit=False;Broker.commits=0
 def test_broker_connection_failure_does_not_write_or_commit(self):
  class Down(Broker):fail_subscribe=True
  with self.assertRaisesRegex(RuntimeError,"connection refused"):
   c.consume_once(db=str(self.db),consumer_factory=Down)
  self.assertFalse(self.db.exists());self.assertEqual(Broker.commits,0)
 def test_broker_poll_error_fails_closed(self):
  class Error(Broker):next_message=Message(error="simulated broker timeout")
  with self.assertRaises(RuntimeError):c.consume_once(db=str(self.db),consumer_factory=Error)
  self.assertFalse(self.db.exists());self.assertEqual(Broker.commits,0)
 def test_db_failure_never_commits_offset(self):
  class Good(Broker):next_message=Message(event())
  class FailingStore:
   def __init__(self,path):pass
   def put(self,evt):raise sqlite3.OperationalError("simulated disk full")
   def close(self):pass
  with patch.object(c,"AggregateStore",FailingStore):
   with self.assertRaisesRegex(sqlite3.OperationalError,"disk full"):
    c.consume_once(db=str(self.db),consumer_factory=Good)
  self.assertEqual(Broker.commits,0)
 def test_duplicate_on_replay_preserves_single_row(self):
  class Replay(Broker):next_message=Message(event())
  first=c.consume_once(db=str(self.db),consumer_factory=Replay)
  second=c.consume_once(db=str(self.db),consumer_factory=Replay)
  self.assertEqual(first["state"],"stored")
  self.assertEqual(second["state"],"duplicate_already_stored")
  self.assertEqual(second["records_in_store"],1)
 def test_commit_failure_is_not_falsely_successful(self):
  class Fail(Broker):
   next_message=Message(event());fail_commit=True
  with self.assertRaisesRegex(RuntimeError,"commit timeout"):
   c.consume_once(db=str(self.db),consumer_factory=Fail)
  store=c.AggregateStore(self.db)
  try:self.assertEqual(store.count(),1)
  finally:store.close()
  self.assertEqual(Broker.commits,0)
 def test_sqlite_backup_restore_and_source_unchanged(self):
  store=c.AggregateStore(self.db)
  try:store.put(event())
  finally:store.close()
  before=self.db.read_bytes()
  result=b.verify_backup(self.db,self.root/"backup")
  self.assertEqual(result["source_records"],1)
  self.assertEqual(result["restored_records"],1)
  self.assertEqual(result["sqlite_integrity"],"ok")
  self.assertFalse(result["source_modified"])
  self.assertEqual(self.db.read_bytes(),before)
 def test_corrupted_source_rejected_with_no_backup(self):
  self.db.write_bytes(b"not-a-valid-sqlite-file")
  with self.assertRaises(sqlite3.DatabaseError):b.verify_backup(self.db,self.root/"backup")
  self.assertFalse(list((self.root/"backup").glob("*.sqlite3")))
 def test_scope_and_no_live_destructive_actions(self):
  text=(ROOT/"scripts/backup_verify_mta.py").read_text()
  self.assertNotIn("aviation.states.v1",text)
  self.assertNotIn("consumer.commit",text)
  self.assertNotIn("docker compose down",text)
