"""Phase 2.2 local Silver/Gold tests, with synthetic tests never claimed as live data."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("tlc_silver_gold", ROOT / "scripts/transform_nyc_tlc.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TLCSilverGoldTests(unittest.TestCase):
    def test_assess_valid_and_invalid_rows(self):
        row = {
            "tpep_pickup_datetime": datetime(2024, 1, 1),
            "tpep_dropoff_datetime": datetime(2024, 1, 1, 0, 15),
            "trip_distance": 3.5, "fare_amount": 12.0, "total_amount": 15.0,
            "PULocationID": 1, "DOLocationID": 2,
        }
        self.assertEqual(module.assess(row), [])
        self.assertIn("invalid_distance", module.assess({**row, "trip_distance": -1.0}))
        self.assertIn("dropoff_before_pickup", module.assess({**row, "tpep_dropoff_datetime": datetime(2023, 1, 1)}))
        self.assertIn("invalid_total_amount", module.assess({**row, "total_amount": float("nan")}))

    def test_requires_validation_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                module.verify_validation(Path(d) / "yellow_tripdata_2024-01.parquet", Path(d) / "missing.json")

    def test_end_to_end_local_medallion(self):
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            self.skipTest("Install optional pyarrow")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            bronze = root / "yellow_tripdata_2024-01.parquet"
            now = datetime(2024, 1, 1, 12)
            fields = {
                "VendorID": [1, 1, 2],
                "tpep_pickup_datetime": [now, now, now],
                "tpep_dropoff_datetime": [now + timedelta(minutes=10), now, now + timedelta(minutes=20)],
                "passenger_count": [1, None, 2],
                "trip_distance": [2.5, -1.0, 3.0],
                "PULocationID": [1, 1, 3],
                "DOLocationID": [2, 3, 4],
                "fare_amount": [10.0, 5.0, 12.0],
                "total_amount": [12.0, 5.0, 15.0],
            }
            pq.write_table(pa.table(fields), bronze)
            raw = bronze.read_bytes()
            checksum = hashlib.sha256(raw).hexdigest()
            (root / (bronze.name + ".manifest.json")).write_text(json.dumps({
                "source": "nyc_tlc_yellow_taxi", "file_name": bronze.name,
                "stage": "bronze_downloaded_unvalidated", "bytes": len(raw),
                "sha256": checksum, "period": "2024-01",
            }), encoding="utf-8")
            report = root / "validated.json"
            report.write_text(json.dumps({
                "source": "nyc_tlc_yellow_taxi", "file_name": bronze.name,
                "period": "2024-01", "source_sha256": checksum,
                "stage": "local_validation_report_only", "row_count": 3,
                "required_schema_validated": True, "complete_row_scan": True,
                "approved_snapshot": None, "published_reporting": False,
            }), encoding="utf-8")
            output = root / "silver_gold"
            result = module.transform(bronze, report, output, batch_size=128)
            self.assertEqual((result["validated_source_rows"], result["silver_rows"], result["quarantined_rows"], result["gold_days"]), (3, 2, 1, 1))
            self.assertEqual(pq.read_table(output / "silver_trips.parquet").num_rows, 2)
            gold = pq.read_table(output / "gold_daily_trips.parquet").to_pylist()
            self.assertEqual(gold[0]["trip_count"], 2)
            self.assertAlmostEqual(gold[0]["trip_distance_sum"], 5.5)
            self.assertEqual(len((output / "rejected_row_reasons.jsonl").read_text().splitlines()), 1)
            self.assertEqual(bronze.read_bytes(), raw)
            with self.assertRaises(FileExistsError):
                module.transform(bronze, report, output, batch_size=128)
            report.write_text(json.dumps({
                "source": "nyc_tlc_yellow_taxi", "file_name": bronze.name, "period": "2024-01",
                "source_sha256": "0" * 64, "stage": "local_validation_report_only",
                "required_schema_validated": True, "complete_row_scan": True,
                "row_count": 3, "approved_snapshot": None, "published_reporting": False,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Validation evidence"):
                module.transform(bronze, report, root / "another_output", batch_size=128)
