"""Read-only NYC TLC historical schema and checksum validation contracts."""
import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("tlc_validate",ROOT/"scripts/validate_nyc_tlc.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TLCHistoricalValidationTests(unittest.TestCase):
 def test_sha256_and_acquisition_identity(self):
  with tempfile.TemporaryDirectory() as folder:
   source=Path(folder)/"yellow_tripdata_2024-01.parquet"
   raw=b"PAR1"+b"sample"+b"PAR1"
   source.write_bytes(raw)
   valid={"source":"nyc_tlc_yellow_taxi","file_name":source.name,"stage":"bronze_downloaded_unvalidated","bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
   module._validate_identity(source,valid)
   with self.assertRaisesRegex(ValueError,"SHA-256 does not match acquisition manifest"):
    module._validate_identity(source,{**valid,"sha256":"0"*64})
   with self.assertRaisesRegex(ValueError,"size"):
    module._validate_identity(source,{**valid,"bytes":len(raw)+1})

 def test_missing_manifest_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   with self.assertRaises(ValueError):
    module._load_manifest(Path(folder)/"missing.manifest.json")

 def test_bounded_numeric_quality_checks(self):
  self.assertFalse(module._numeric(None))
  self.assertFalse(module._numeric(True))
  self.assertFalse(module._numeric(float("nan")))
  self.assertFalse(module._numeric(float("inf")))
  self.assertTrue(module._numeric(1.5))

 def test_real_parquet_scan_if_pyarrow_is_installed(self):
  try:
   import pyarrow as pa
   import pyarrow.parquet as pq
  except ImportError:
   self.skipTest("Optional pyarrow not installed; run python -m pip install pyarrow")
  from datetime import datetime, timedelta
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   source=root/"yellow_tripdata_2024-01.parquet"
   values={
    "VendorID":[1,1],"tpep_pickup_datetime":[datetime(2024,1,1),datetime(2024,1,2)],
    "tpep_dropoff_datetime":[datetime(2024,1,1,0,10),datetime(2024,1,1,23,0)],
    "passenger_count":[1,2],"trip_distance":[1.5,-1.0],
    "PULocationID":[1,2],"DOLocationID":[3,4],
    "fare_amount":[10.0,12.0],"total_amount":[13.0,15.0]}
   pq.write_table(pa.table(values),source)
   original=source.read_bytes()
   manifest={"source":"nyc_tlc_yellow_taxi","file_name":source.name,"stage":"bronze_downloaded_unvalidated","bytes":len(original),"sha256":hashlib.sha256(original).hexdigest(),"period":"2024-01"}
   (root/(source.name+".manifest.json")).write_text(json.dumps(manifest),encoding="utf-8")
   report=module.validate_file(source,root/"reports",batch_size=128)
   self.assertEqual(report["row_count"],2)
   self.assertEqual(report["quality_warning_counts"]["invalid_trip_distance"],1)
   self.assertEqual(report["quality_warning_counts"]["dropoff_before_pickup"],1)
   self.assertEqual(source.read_bytes(),original)
   self.assertEqual(json.loads((root/"reports"/(source.name+".validation.json")).read_text())["row_count"],2)
   with self.assertRaises(FileExistsError):
    module.validate_file(source,root/"reports",batch_size=128)
