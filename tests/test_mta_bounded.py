"""Phase 3.5 bounded runner contracts. No external API / Kafka required."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("mta_bounded",ROOT/"scripts/run_mta_bounded.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RunnerTests(unittest.TestCase):
 def sample(self):
  return {"source":"mta_nyct_subway_gtfs_rt",
    "stage":"local_provider_connectivity_validation_only","freshness_state":"fresh",
    "valid_gtfs_entities":True,"feed_id":"ace","provider_timestamp_utc":"2026-11-26T11:55:41+00:00",
    "observed_at_utc":"2026-11-26T11:55:43+00:00","response_sha256":"a"*64,
    "entities":124,"trip_updates":62,"vehicle_positions":62,"alerts":0}
 def test_dry_run_makes_no_provider_or_kafka_calls(self):
  def forbidden(*a,**kw):raise AssertionError("unexpected external action")
  result=m.run(execute=False,fetcher=forbidden,publisher=forbidden,consumer=forbidden)
  self.assertEqual(result["state"],"plan_only")
  self.assertFalse(result["network_requested"])
 def test_schedule_limits(self):
  for cycles,interval in ((0,120),(4,120),(1,59),(1,3601)):
   with self.assertRaises(ValueError):m.validate_schedule(cycles,interval)
  self.assertEqual(m.validate_schedule(3,60)["max_provider_requests"],3)
 def test_one_verified_cycle(self):
  evidence=self.sample()
  from publish_mta_aggregate import event_from_evidence
  event=event_from_evidence(evidence)
  def fetch(feed):self.assertEqual(feed,"ace");return evidence
  def publish(payload):self.assertEqual(payload["event_id"],event["event_id"]);return {"partition":0,"offset":7}
  def consume(**kw):return {"state":"stored","event_id":event["event_id"],"offset_committed":True}
  result=m.run(execute=True,fetcher=fetch,publisher=publish,consumer=consume)
  self.assertEqual(result["state"],"bounded_cycle_verified")
  self.assertTrue(result["observations"][0]["consumer_event_matches_publish"])
 def test_backlog_does_not_claim_success(self):
  evidence=self.sample()
  def fetch(feed):return evidence
  def publish(event):return {"partition":0,"offset":8}
  def consume(**kw):return {"state":"stored","event_id":"b"*64,"offset_committed":True}
  outcome=m.run(cycles=2,execute=True,fetcher=fetch,publisher=publish,consumer=consume,sleeper=lambda n:None)
  self.assertEqual(outcome["state"],"attention_required")
  self.assertEqual(outcome["completed_cycles"],1)
 def test_no_daemon_loop_or_aviation_topic(self):
  code=(ROOT/"scripts/run_mta_bounded.py").read_text()
  self.assertNotIn("while True",code)
  self.assertNotIn("aviation.states.v1",code)
