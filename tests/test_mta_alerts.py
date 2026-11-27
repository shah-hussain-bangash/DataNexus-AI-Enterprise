"""Phase 3.7 alert thresholds and simulated recovery evidence (no Kafka)."""
import importlib.util
import sys
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("mta_alert",ROOT/"scripts/assess_mta_alerts.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
NOW=datetime(2026,11,27,12,0,tzinfo=timezone.utc)
def report():
 stamp=NOW-timedelta(seconds=20)
 return {"state":"local_monitor_snapshot","checked_at_utc":stamp.isoformat(),
 "latest_provider_timestamp_utc":(stamp-timedelta(seconds=40)).isoformat(),
 "topic":"mta.subway.updates.v1","group":"datanexus-mta-aggregate-v1",
 "production_approved":False,"source_api_checked_now":False,
 "offset_state":"valid","low_offset":0,"high_offset_exclusive":6,
 "committed_next_offset":6,"consumer_lag_messages":0,
 "latest_stored_source_age_seconds":40}
class MtaAlertTests(unittest.TestCase):
 def test_healthy_snapshot_does_not_claim_live_health(self):
  out=m.assess(report(),NOW)
  self.assertEqual(out["alert_count"],0)
  self.assertFalse(out["automatic_recovery_performed"])
  self.assertFalse(out["production_approved"])
 def test_old_snapshot_and_old_source_flagged_separately(self):
  r=report()
  r["checked_at_utc"]=(NOW-timedelta(minutes=15)).isoformat()
  r["latest_provider_timestamp_utc"]=(NOW-timedelta(minutes=25)).isoformat()
  r["latest_stored_source_age_seconds"]=600
  out=m.assess(r,NOW)
  self.assertEqual({x["code"] for x in out["alerts"]},{"MONITOR_STALE","STORED_OBSERVATION_OLD"})
 def test_lag_critical_and_minor(self):
  r=report();r["committed_next_offset"]=3;r["consumer_lag_messages"]=3
  self.assertEqual(m.assess(r,NOW)["status"],"attention")
  r["high_offset_exclusive"]=15;r["consumer_lag_messages"]=12
  self.assertEqual(m.assess(r,NOW)["status"],"critical")
 def test_unknown_offset_never_treated_as_zero(self):
  r=report();r["offset_state"]="unknown_uncommitted";r["committed_next_offset"]=None;r["consumer_lag_messages"]=None
  alerts=m.assess(r,NOW)["alerts"]
  self.assertEqual(alerts[0]["code"],"OFFSET_UNKNOWN")
  self.assertEqual(alerts[0]["severity"],"critical")
 def test_inconsistent_metrics_fail_closed(self):
  r=report();r["consumer_lag_messages"]=2
  with self.assertRaisesRegex(ValueError,"arithmetic"):m.assess(r,NOW)
  r=report();r["production_approved"]=True
  with self.assertRaises(ValueError):m.assess(r,NOW)
 def test_no_reset_replay_or_aviation_mutation(self):
  code=(ROOT/"scripts/assess_mta_alerts.py").read_text(encoding="utf-8")
  self.assertNotIn("aviation.states.v1",code)
  self.assertNotIn("consumer.commit(",code)
  self.assertNotIn("seek(",code)
