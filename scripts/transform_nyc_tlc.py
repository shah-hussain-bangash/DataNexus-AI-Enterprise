"""Phase 2.2: fail-closed LOCAL NYC TLC Silver and Gold transformation.

Input: previously checksummed Bronze Parquet plus Phase 2.1 validation report.
Output: local Silver Parquet, rejected-row reasons and daily Gold Parquet.
No production approval, live API integration, or tenant sharing is implied.
"""
import argparse
import json
import math
import os
import shutil
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from validate_nyc_tlc import REQUIRED, _load_manifest, _validate_identity, _numeric


def verify_validation(source, report_path):
    report_path = Path(report_path)
    if not report_path.is_file() or report_path.is_symlink() or report_path.stat().st_size > 65536:
        raise ValueError("Phase 2.1 validation report missing or invalid")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("Phase 2.1 validation report malformed")
    manifest = _load_manifest(source.with_name(source.name + ".manifest.json"))
    checksum = _validate_identity(source, manifest)
    expected = {
        "source": "nyc_tlc_yellow_taxi",
        "file_name": source.name,
        "period": manifest.get("period"),
        "source_sha256": checksum,
        "stage": "local_validation_report_only",
        "required_schema_validated": True,
        "complete_row_scan": True,
        "approved_snapshot": None,
        "published_reporting": False,
    }
    if any(report.get(key) != value for key, value in expected.items()):
        raise ValueError("Validation evidence does not match current Bronze source")
    if type(report.get("row_count")) is not int or report["row_count"] < 0:
        raise ValueError("Validation report has no trustworthy row count")
    return report, checksum


def assess(row):
    """Return rejection reasons. Missing optional passenger_count is tolerated.

    A nonnegative fare or total can include zero. Negative monetary values are
    excluded from this *local analytics subset* pending a documented refund policy.
    """
    reasons = []
    start, end = row["tpep_pickup_datetime"], row["tpep_dropoff_datetime"]
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        reasons.append("missing_datetime")
    elif end < start:
        reasons.append("dropoff_before_pickup")
    distance = row["trip_distance"]
    if not _numeric(distance) or distance < 0:
        reasons.append("invalid_distance")
    for name in ("fare_amount", "total_amount"):
        if not _numeric(row[name]) or row[name] < 0:
            reasons.append("invalid_" + name)
    for name in ("PULocationID", "DOLocationID"):
        loc = row[name]
        if isinstance(loc, bool) or not isinstance(loc, int) or loc <= 0:
            reasons.append("invalid_" + name)
    if isinstance(start, datetime) and isinstance(end, datetime) and end >= start:
        try:
            if (end - start).total_seconds() > 48 * 3600:
                reasons.append("duration_over_48_hours")
        except (OverflowError, ValueError):
            reasons.append("invalid_duration")
    return reasons


def transform(source_file, validation_file, output_dir, batch_size=16384):
    """Create an isolated local dataset, refusing unvalidated or modified inputs."""
    if not 128 <= batch_size <= 65536:
        raise ValueError("batch_size outside 128..65536")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Install pyarrow: python -m pip install pyarrow") from exc
    source = Path(source_file).resolve()
    output = Path(output_dir).resolve()
    report, checksum = verify_validation(source, validation_file)
    if output.exists():
        raise FileExistsError("Refusing to overwrite an existing Silver/Gold output directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".tlc-silver-gold-", dir=output.parent))
    scan_count = accepted = rejected = 0
    reasons = defaultdict(int)
    gold = defaultdict(lambda: {"trip_count": 0, "distance_sum": 0.0, "total_amount_sum": 0.0})
    columns = sorted(REQUIRED)
    # Explicit schemas keep even zero-row outputs queryable, without fake records.
    silver_schema = pa.schema([
        ("source_row_index", pa.int64()), ("pickup_date", pa.date32()),
        ("PULocationID", pa.int32()), ("DOLocationID", pa.int32()),
        ("trip_distance", pa.float64()), ("fare_amount", pa.float64()),
        ("total_amount", pa.float64()), ("duration_minutes", pa.float64()),
    ])
    gold_schema = pa.schema([
        ("pickup_date", pa.date32()), ("trip_count", pa.int64()),
        ("trip_distance_sum", pa.float64()), ("total_amount_sum", pa.float64()),
    ])
    writer = None
    try:
        parquet = pq.ParquetFile(source)
        if not REQUIRED.issubset(parquet.schema_arrow.names):
            raise ValueError("Bronze schema no longer matches expected columns")
        with (staging / "rejected_row_reasons.jsonl").open("w", encoding="utf-8") as rejected_file:
            for batch in parquet.iter_batches(batch_size=batch_size, columns=columns):
                rows = batch.to_pylist()
                clean = []
                for row in rows:
                    index = scan_count
                    scan_count += 1
                    issues = assess(row)
                    if issues:
                        rejected += 1
                        for reason in issues:
                            reasons[reason] += 1
                        # No raw trip payload is written to the rejection log.
                        rejected_file.write(json.dumps({"source_row_index": index, "reasons": issues}) + "\n")
                        continue
                    accepted += 1
                    pickup = row["tpep_pickup_datetime"]
                    day = pickup.date()
                    distance = float(row["trip_distance"])
                    total = float(row["total_amount"])
                    metrics = gold[day]
                    metrics["trip_count"] += 1
                    metrics["distance_sum"] += distance
                    metrics["total_amount_sum"] += total
                    clean.append({
                        "source_row_index": index,
                        "pickup_date": day,
                        "PULocationID": int(row["PULocationID"]),
                        "DOLocationID": int(row["DOLocationID"]),
                        "trip_distance": distance,
                        "fare_amount": float(row["fare_amount"]),
                        "total_amount": total,
                        "duration_minutes": (row["tpep_dropoff_datetime"] - pickup).total_seconds() / 60.0,
                    })
                if clean:
                    if writer is None:
                        writer = pq.ParquetWriter(staging / "silver_trips.parquet", silver_schema)
                    writer.write_table(pa.Table.from_pylist(clean, schema=silver_schema))
        if writer is not None:
            writer.close()
            writer = None
        else:
            pq.write_table(pa.Table.from_pylist([], schema=silver_schema), staging / "silver_trips.parquet")
        if scan_count != report["row_count"] or accepted + rejected != scan_count:
            raise ValueError("Silver/Gold row reconciliation failed against validated source")
        daily = [{"pickup_date": day, "trip_count": row["trip_count"],
                  "trip_distance_sum": row["distance_sum"], "total_amount_sum": row["total_amount_sum"]}
                 for day, row in sorted(gold.items())]
        pq.write_table(pa.Table.from_pylist(daily, schema=gold_schema), staging / "gold_daily_trips.parquet")
        if sum(x["trip_count"] for x in daily) != accepted:
            raise ValueError("Gold aggregation does not reconcile with Silver")
        summary = {
            "stage": "local_unapproved_silver_gold",
            "source": "nyc_tlc_yellow_taxi",
            "period": report["period"],
            "source_file": source.name,
            "source_sha256": checksum,
            "validated_source_rows": scan_count,
            "silver_rows": accepted,
            "quarantined_rows": rejected,
            "gold_days": len(daily),
            "rejection_reasons": dict(sorted(reasons.items())),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "approved_snapshot": None, "license_review": "pending",
            "published_reporting": False, "enterprise_accepted": False,
            "caveat": "Local prototype artifacts only. No live service, tenant access policy, or release approval.",
        }
        (staging / "transform_manifest.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        staging.rename(output)
        return summary
    finally:
        if writer is not None:
            writer.close()
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default="data/dev/nyc_tlc/yellow_tripdata_2024-01.parquet")
    parser.add_argument("--validation", default="data/dev/nyc_tlc/validation/yellow_tripdata_2024-01.parquet.validation.json")
    parser.add_argument("--output", default="data/dev/nyc_tlc/silver_gold_2024_01")
    parser.add_argument("--batch-size", type=int, default=16384)
    args = parser.parse_args()
    print(json.dumps(transform(args.file, args.validation, args.output, args.batch_size), indent=2))


if __name__ == "__main__":
    main()
