"""Phase 2: read-only NYC TLC Yellow Taxi Parquet validation.

Requires optional dependency: python -m pip install pyarrow
The source Parquet and its Bronze acquisition manifest are never modified.
A report is published only after the entire Parquet file is scanned.
"""
import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES = 180 * 1024 * 1024
FILE_NAME = re.compile(r"^yellow_tripdata_(20\d{2})-(0[1-9]|1[0-2])\.parquet$")
REQUIRED = {
    "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "passenger_count", "trip_distance", "PULocationID",
    "DOLocationID", "fare_amount", "total_amount"
}
NUMERIC = {"passenger_count", "trip_distance", "PULocationID", "DOLocationID", "fare_amount", "total_amount"}
REASON_LIMIT = 12


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 16384:
        raise ValueError("Valid raw Bronze manifest is required")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Malformed Bronze manifest")
    return value


def _validate_identity(source, manifest):
    if source.is_symlink() or not source.is_file():
        raise ValueError("A regular Parquet file is required")
    if not FILE_NAME.fullmatch(source.name):
        raise ValueError("File is not an expected NYC TLC Yellow Taxi monthly Parquet")
    if source.stat().st_size > MAX_BYTES or source.stat().st_size < 12:
        raise ValueError("Unexpected raw file size")
    if manifest.get("source") != "nyc_tlc_yellow_taxi":
        raise ValueError("Source identity mismatch")
    if manifest.get("file_name") != source.name or manifest.get("stage") != "bronze_downloaded_unvalidated":
        raise ValueError("Not a valid unchanged Bronze acquisition")
    if manifest.get("bytes") != source.stat().st_size:
        raise ValueError("Source size differs from acquisition manifest")
    digest = manifest.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
        raise ValueError("Invalid acquisition checksum")
    actual = _sha256(source)
    if actual != digest:
        raise ValueError("Raw Parquet SHA-256 does not match acquisition manifest")
    return actual


def _numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_file(file_path, report_dir, batch_size=16384):
    """Validate one month; return summary without exposing individual trip records.

    Row-level anomalies are counted, not silently excluded from source totals.
    This is a local data-quality report, not a licensed/published Gold dataset.
    """
    if not 128 <= batch_size <= 65536:
        raise ValueError("batch_size must be between 128 and 65536")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Install pyarrow: python -m pip install pyarrow") from exc
    source = Path(file_path).resolve()
    manifest_path = source.with_name(source.name + ".manifest.json")
    manifest = _load_manifest(manifest_path)
    digest = _validate_identity(source, manifest)
    parquet = pq.ParquetFile(source)
    columns = set(parquet.schema_arrow.names)
    missing = sorted(REQUIRED - columns)
    if missing:
        raise ValueError("Missing required taxi-trip columns: " + ", ".join(missing))
    for name in ("tpep_pickup_datetime", "tpep_dropoff_datetime"):
        if not pa.types.is_timestamp(parquet.schema_arrow.field(name).type):
            raise ValueError(name + " must be a timestamp")
    for name in NUMERIC:
        typ = parquet.schema_arrow.field(name).type
        if not (pa.types.is_integer(typ) or pa.types.is_floating(typ) or pa.types.is_decimal(typ)):
            raise ValueError(name + " must be numeric")
    counts = Counter()
    row_total = 0
    # Only scan a bounded set of columns; retain no row samples or passenger information.
    scan_columns = sorted(REQUIRED)
    for batch in parquet.iter_batches(batch_size=batch_size, columns=scan_columns):
        cols = batch.to_pydict()
        for index in range(batch.num_rows):
            row_total += 1
            pickup = cols["tpep_pickup_datetime"][index]
            dropoff = cols["tpep_dropoff_datetime"][index]
            if pickup is None or dropoff is None:
                counts["missing_datetime"] += 1
            elif dropoff < pickup:
                counts["dropoff_before_pickup"] += 1
            distance = cols["trip_distance"][index]
            if not _numeric(distance) or distance < 0:
                counts["invalid_trip_distance"] += 1
            fare = cols["fare_amount"][index]
            if not _numeric(fare):
                counts["invalid_fare"] += 1
            total = cols["total_amount"][index]
            if not _numeric(total):
                counts["invalid_total_amount"] += 1
            pu = cols["PULocationID"][index]
            do = cols["DOLocationID"][index]
            if not _numeric(pu) or pu <= 0 or not _numeric(do) or do <= 0:
                counts["invalid_location_ids"] += 1
            if any(cols[name][index] is None for name in REQUIRED):
                counts["missing_required_values"] += 1
    if row_total != parquet.metadata.num_rows:
        raise ValueError("Row scan does not reconcile with Parquet footer")
    report = {
        "source": "nyc_tlc_yellow_taxi",
        "file_name": source.name,
        "period": manifest.get("period"),
        "source_sha256": digest,
        "bytes": source.stat().st_size,
        "row_count": row_total,
        "row_groups": parquet.num_row_groups,
        "columns": sorted(columns),
        "required_schema_validated": True,
        "complete_row_scan": True,
        "quality_warning_counts": dict(sorted(counts.items())),
        "has_quality_warnings": bool(counts),
        "scan_completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "local_validation_report_only",
        "license_review": "pending",
        "approved_snapshot": None,
        "published_reporting": False,
        "enterprise_accepted": False,
    }
    target_dir = Path(report_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / (source.name + ".validation.json")
    if target.exists():
        raise FileExistsError("Existing validation report; inspect or move it before rerun")
    fd, tmp = tempfile.mkstemp(dir=target_dir, prefix=".partial-validation-", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default="data/dev/nyc_tlc/yellow_tripdata_2024-01.parquet")
    parser.add_argument("--output", default="data/dev/nyc_tlc/validation")
    parser.add_argument("--batch-size", type=int, default=16384)
    args = parser.parse_args()
    print(json.dumps(validate_file(args.file, args.output, args.batch_size), indent=2))


if __name__ == "__main__":
    main()
