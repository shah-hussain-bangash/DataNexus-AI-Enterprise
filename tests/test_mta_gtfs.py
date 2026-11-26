"""MTA Phase 3.1 validation contracts: synthetic data, NO network requests."""
import importlib.util
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("mta_collect",ROOT/"scripts/collect_mta_gtfs.py")
collector=importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

class FakeEntity:
 def __init__(self,id,fields=("trip_update",)):
  self.id=id;self.fields=set(fields)
 def HasField(self,key):return key in self.fields

class MTAGTFSValidationTests(unittest.TestCase):
 def setUp(self):
  self.now=datetime(2026,11,26,12,tzinfo=timezone.utc)
  self.timestamp=int(self.now.timestamp())
 def message(self,ids=("a","b"),offset=0):
  return SimpleNamespace(
   header=SimpleNamespace(timestamp=self.timestamp+offset),
   entity=[FakeEntity(id) for id in ids],
  )
 def test_actual_feed_id_allowlist(self):
  self.assertEqual(set(collector.FEEDS),{"ace","1234567"})
  self.assertTrue(all(x.startswith("https://api-endpoint.mta.info/") for x in collector.FEEDS.values()))
  with self.assertRaises(ValueError):
   collector.fetch_feed("https://untrusted.test/evil")
 def test_valid_event_counts_and_freshness(self):
  result=collector.validate_message(self.message(),self.now)
  self.assertEqual(result["entities"],2)
  self.assertEqual(result["trip_updates"],2)
  self.assertEqual(result["freshness_state"],"fresh")
  self.assertTrue(result["valid_gtfs_entities"])
 def test_duplicate_and_invalid_payload_fail_closed(self):
  with self.assertRaisesRegex(ValueError,"identity"):
   collector.validate_message(self.message(ids=("a","a")),self.now)
  with self.assertRaisesRegex(ValueError,"identity"):
   collector.validate_message(self.message(ids=("",)),self.now)
  with self.assertRaisesRegex(ValueError,"no entities"):
   collector.validate_message(self.message(ids=()),self.now)
 def test_age_and_future_bounds(self):
  stale=collector.validate_message(self.message(offset=-7201),self.now)
  self.assertEqual(stale["freshness_state"],"stale_over_2h")
  with self.assertRaisesRegex(ValueError,"future"):
   collector.validate_message(self.message(offset=301),self.now)
  with self.assertRaisesRegex(ValueError,"timestamp"):
   collector.validate_message(self.message(offset=-self.timestamp),self.now)
 def test_no_raw_data_or_kafka_in_collector(self):
  source=(ROOT/"scripts/collect_mta_gtfs.py").read_text(encoding="utf-8")
  self.assertIn('"raw_payload_stored":False',source)
  self.assertIn('"kafka_published":False',source)
  self.assertNotIn("confluent_kafka",source)
  self.assertNotIn("while True",source)
