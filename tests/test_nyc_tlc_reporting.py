"""Local historical reporting source contracts."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"apps/api"))
def load(file,name):
 spec=importlib.util.spec_from_file_location(name,ROOT/file)
 obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
publisher=load("scripts/export_nyc_tlc_reporting.py","tlc_report_export")
api=load("apps/api/tlc_reporting.py","tlc_reporting")

class LocalReportingTests(unittest.TestCase):
 def test_missing_data_is_never_fabricated(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(FileNotFoundError):
    api.read_preview(d)
   with self.assertRaises(ValueError):
    api.read_preview(d,"2024-02")
 def test_protected_routes_and_local_mount(self):
  main=(ROOT/"apps/api/main.py").read_text()
  self.assertIn('"/api/v1/nyc-tlc/reporting"',main)
  self.assertIn('require_permission("catalog:read")',main)
  proxy=(ROOT/"apps/web/app/api/portal/[...path]/route.ts").read_text()
  self.assertIn('"nyc-tlc/reporting"',proxy)
  docker=(ROOT/"apps/api/Dockerfile").read_text()
  self.assertIn("tlc_reporting.py",docker)
 def test_published_report_reconciles_and_rejects_tampering(self):
  try:
   import pyarrow as pa
   import pyarrow.parquet as pq
  except ImportError:
   self.skipTest("Optional PyArrow not installed")
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/"nyc_tlc"/"silver_gold_2024_01"
   root.mkdir(parents=True)
   silver=root/"silver_trips.parquet";gold=root/"gold_daily_trips.parquet"
   pq.write_table(pa.table({"pickup_date":[datetime(2024,1,2).date(),datetime(2024,2,1).date()],
                             "trip_count":[2,1],"trip_distance_sum":[3.0,1.0],"total_amount_sum":[20.0,8.0]}),gold)
   pq.write_table(pa.table({"source_row_index":[0,1,2]}),silver)
   (root/"rejected_row_reasons.jsonl").write_text("","utf-8")
   (root/"transform_manifest.json").write_text(json.dumps({"stage":"local_unapproved_silver_gold","source":"nyc_tlc_yellow_taxi","period":"2024-01","validated_source_rows":3,"silver_rows":3,"quarantined_rows":0,"gold_days":2,"source_sha256":"a"*64}))
   snapshot=publisher.build_snapshot(root)
   self.assertEqual(snapshot["outside_month_trip_count"],1)
   self.assertEqual(snapshot["in_month_trip_count"],2)
   self.assertEqual(api.read_preview(Path(d))["silver_rows"],3)
   with self.assertRaises(FileExistsError):publisher.build_snapshot(root)
   (root/"transform_manifest.json").write_text('{"stage":"tampered"}')
   with self.assertRaisesRegex(ValueError,"modified"):
    api.read_preview(d)
