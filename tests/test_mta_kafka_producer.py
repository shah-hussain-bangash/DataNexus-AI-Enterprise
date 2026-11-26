"""Phase 3.2 one-shot MTA aggregate producer; no broker or network required."""
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("mta_producer",ROOT/"scripts/publish_mta_aggregate.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def sample():
 return {"source":"mta_nyct_subway_gtfs_rt","stage":"local_provider_connectivity_validation_only",
 "freshness_state":"fresh","valid_gtfs_entities":True,"feed_id":"ace",
 "provider_timestamp_utc":"2026-11-26T11:19:06+00:00","observed_at_utc":"2026-11-26T11:19:10+00:00",
 "response_sha256":"a"*64,"entities":110,"trip_updates":55,"vehicle_positions":55,"alerts":0}

class Message:
 def partition(self):return 0
 def offset(self):return 3

class FakeProducer:
 def __init__(self,config):self.config=config;self.records=[]
 def list_topics(self,timeout):
  return type("Metadata",(),{"topics":{mod.TOPIC:type("T",(),{"error":None})()}})()
 def produce(self,topic,key,value,on_delivery):
  self.records.append((topic,key,value));on_delivery(None,Message())
 def flush(self,timeout):return 0

class ProducerTests(unittest.TestCase):
 def test_aggregate_contains_no_trip_vehicle_ids(self):
  event=mod.event_from_evidence(sample())
  self.assertEqual(event["counts"]["entities"],110)
  self.assertNotIn("trip_id",str(event))
  self.assertEqual(event["kind"],"one_shot_aggregate")
  self.assertEqual(event["event_id"],mod.event_from_evidence(sample())["event_id"])
 def test_freshness_validation_required(self):
  bad=sample();bad["freshness_state"]="stale_over_2h"
  with self.assertRaisesRegex(ValueError,"fresh"):mod.event_from_evidence(bad)
  bad=sample();bad["entities"]=-1
  with self.assertRaises(ValueError):mod.event_from_evidence(bad)
 def test_explicit_local_broker_only_and_delivery(self):
  event=mod.event_from_evidence(sample())
  with self.assertRaises(ValueError):mod.publish_once(event,"example.com:9092",FakeProducer)
  result=mod.publish_once(event,producer_factory=FakeProducer)
  self.assertEqual(result,{"partition":0,"offset":3})
 def test_topic_and_one_shot_contract(self):
  text=(ROOT/"scripts/publish_mta_aggregate.py").read_text(encoding="utf-8")
  self.assertIn('parser.add_argument("--publish",action="store_true"',text)
  self.assertIn('TOPIC="mta.subway.updates.v1"',text)
  self.assertNotIn("while True",text)
  self.assertNotIn("aviation.states.v1",text)
