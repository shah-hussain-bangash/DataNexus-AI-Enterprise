"""Phase 3.3 MTA Kafka consumer tests, no live broker or HTTP."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("mta_consumer",ROOT/"scripts/consume_mta_aggregate.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def sample():
 return {"event_id":"a"*64,"schema_version":"1.0","source":"mta_nyct_subway_gtfs_rt",
 "feed_id":"ace","provider_timestamp_utc":"2026-11-26T11:55:41+00:00",
 "observed_at_utc":"2026-11-26T11:55:43+00:00",
 "provider_response_sha256":"b"*64,
 "counts":{"entities":124,"trip_updates":62,"vehicle_positions":62,"alerts":0},
 "kind":"one_shot_aggregate","production_approved":False}

class MockMessage:
 def __init__(self,event):
  self.event=event
 def value(self):return json.dumps(self.event).encode()
 def key(self):return self.event["event_id"].encode()
 def topic(self):return mod.TOPIC
 def partition(self):return 0
 def offset(self):return 0
 def error(self):return None

class FakeConsumer:
 event=None
 commits=0
 def __init__(self,config):
  self.config=config
  self.closed=False
 def subscribe(self,topics):self.topics=topics
 def poll(self,timeout):return MockMessage(self.event) if self.event else None
 def commit(self,message,asynchronous):self.commits+=1
 def close(self):self.closed=True

class MTAConsumerTests(unittest.TestCase):
 def test_validates_aggregate_schema(self):
  self.assertEqual(mod.verify_event(sample())["counts"]["entities"],124)
  broken=sample();broken["counts"]["trip_updates"]=150
  with self.assertRaises(ValueError):mod.verify_event(broken)
  broken=sample();broken["extra"]="private_raw_data"
  with self.assertRaises(ValueError):mod.verify_event(broken)
 def test_sqlite_idempotent_across_restart(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/"mta.sqlite3"
   a=mod.AggregateStore(path)
   self.assertTrue(a.put(sample()))
   self.assertFalse(a.put(sample()))
   a.close()
   b=mod.AggregateStore(path)
   self.assertEqual(b.count(),1)
   self.assertFalse(b.put(sample()))
   b.close()
 def test_consume_one_event_and_commit_after_storage(self):
  with tempfile.TemporaryDirectory() as directory:
   FakeConsumer.event=sample()
   result=mod.consume_once(db=str(Path(directory)/"events.db"),consumer_factory=FakeConsumer)
   self.assertEqual(result["state"],"stored")
   self.assertTrue(result["offset_committed"])
   self.assertEqual(result["records_in_store"],1)
 def test_poison_event_does_not_commit(self):
  with tempfile.TemporaryDirectory() as directory:
   malformed=sample();malformed["event_id"]="invalid"
   FakeConsumer.event=malformed
   class NoCommit(FakeConsumer):
    def commit(self,**kwargs):raise AssertionError("Poison event committed")
   with self.assertRaises(ValueError):
    mod.consume_once(db=str(Path(directory)/"events.db"),consumer_factory=NoCommit)
 def test_no_messages_no_fake_data(self):
  FakeConsumer.event=None
  with tempfile.TemporaryDirectory() as directory:
   result=mod.consume_once(db=str(Path(directory)/"events.db"),consumer_factory=FakeConsumer)
   self.assertEqual(result["state"],"no_event_available")
   self.assertFalse(result["offset_committed"])
   self.assertFalse((Path(directory)/"events.db").exists())
 def test_separate_topic_and_local_store(self):
  self.assertEqual(mod.TOPIC,"mta.subway.updates.v1")
  self.assertNotEqual(mod.DB,"data/dev/aviation.sqlite3")
  self.assertNotIn("while True",(ROOT/"scripts/consume_mta_aggregate.py").read_text())
