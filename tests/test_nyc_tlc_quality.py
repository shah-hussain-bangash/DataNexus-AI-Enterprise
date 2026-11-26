"""Phase 2.5 monitor unit and fail-closed contract checks."""
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"apps/api"))
spec=importlib.util.spec_from_file_location("tlc_quality",ROOT/"apps/api/tlc_quality.py")
quality=importlib.util.module_from_spec(spec)
spec.loader.exec_module(quality)


class LocalQualityEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)/"nyc_tlc"
  self.folder=self.root/"silver_gold_2024_01"
  self.folder.mkdir(parents=True)
  (self.root/"validation").mkdir()
  self.now=datetime(2026,11,26,12,tzinfo=timezone.utc)
  self.report={
    "source_month":"2024-01","source_sha256":"a"*64,"validated_source_rows":100,
    "silver_rows":90,"quarantined_rows":10,"outside_month_trip_count":2,
    "generated_at_utc":(self.now-timedelta(hours=8)).isoformat(),
  }
  self.validation={
    "source":"nyc_tlc_yellow_taxi","file_name":"yellow_tripdata_2024-01.parquet",
    "stage":"local_validation_report_only","source_sha256":"a"*64,"row_count":100,
    "required_schema_validated":True,"complete_row_scan":True,
    "scan_completed_at_utc":(self.now-timedelta(hours=10)).isoformat(),
    "quality_warning_counts":{"missing_required_values":20},
  }
  self.transform={"validated_source_rows":100,"quarantined_rows":10,
                  "rejection_reasons":{"invalid_fare_amount":8,"invalid_total_amount":5}}
  self.write()
 def write(self):
  (self.root/"validation"/"yellow_tripdata_2024-01.parquet.validation.json").write_text(json.dumps(self.validation))
  (self.folder/"transform_manifest.json").write_text(json.dumps(self.transform))
 def run_monitor(self):
  with patch.object(quality,"read_preview",return_value=self.report):
   return quality.quality_evidence(self.temp.name,now=self.now)
 def test_verified_counts_warn_without_equating_warning_count_to_rejection(self):
  result=self.run_monitor()
  self.assertTrue(result["reconciliation_ok"])
  self.assertEqual(result["accepted_percent"],90)
  self.assertEqual(result["quarantined_percent"],10)
  self.assertEqual(result["validation_warning_counts"]["missing_required_values"],20)
  self.assertEqual(result["report_age_hours"],8)
  self.assertIsNone(result["live_source_freshness"])
  self.assertFalse(result["production_approved"])
 def test_mismatched_source_digest_fails_closed(self):
  self.validation["source_sha256"]="b"*64
  self.write()
  with self.assertRaisesRegex(ValueError,"does not reconcile"):self.run_monitor()
 def test_future_or_untrusted_evidence_fails_closed(self):
  self.report["generated_at_utc"]=(self.now+timedelta(hours=2)).isoformat()
  with self.assertRaisesRegex(ValueError,"future"):self.run_monitor()
  self.report["generated_at_utc"]=(self.now-timedelta(hours=1)).isoformat()
  self.transform["quarantined_rows"]=9
  self.write()
  with self.assertRaisesRegex(ValueError,"do not reconcile"):self.run_monitor()
 def test_secure_api_route_and_proxy(self):
  main=(ROOT/"apps/api/main.py").read_text()
  proxy=(ROOT/"apps/web/app/api/portal/[...path]/route.ts").read_text()
  docker=(ROOT/"apps/api/Dockerfile").read_text()
  self.assertIn('"/api/v1/nyc-tlc/quality"',main)
  self.assertIn('require_permission("quality:read")',main)
  self.assertIn('"nyc-tlc/quality"',proxy)
  self.assertIn("tlc_quality.py",docker)
