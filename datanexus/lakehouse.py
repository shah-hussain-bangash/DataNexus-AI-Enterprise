"""Phase 2B local medallion export (JSONL reference, not Spark or Iceberg).

Reads the committed Phase 2A SQLite sink. Creates Bronze, Silver, quarantine and
Gold artifacts via atomic file replacement for reproducible local verification.
The output is intentionally a small-scale baseline before distributed streaming.
"""
import argparse
import json
import os
import sqlite3
import tempfile
from collections import defaultdict
from contextlib import closing
from datetime import datetime
from pathlib import Path

from datanexus.events import validate_envelope


def _atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="._datanexus_", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _jsonlines(items):
    return "".join(json.dumps(item, sort_keys=True, allow_nan=False) + "\n" for item in items)


def _quality_check(event):
    try:
        validate_envelope(event)
        payload = event["payload"]
        lat = payload.get("latitude")
        lon = payload.get("longitude")
        if not isinstance(payload.get("icao24"), str) or not payload["icao24"].strip():
            return "missing_icao24"
        if isinstance(lat, bool) or isinstance(lon, bool) or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            return "missing_coordinates"
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return "invalid_coordinates"
        timestamp = datetime.fromisoformat(event["source_event_time"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            return "naive_event_time"
        return None
    except (TypeError, ValueError, KeyError, OverflowError):
        return "invalid_envelope"


def export_layers(db_path, output_dir):
    """Export local deterministic snapshots. Returns a summary dict.

    This does not consume a Kafka stream or meet distributed lakehouse guarantees.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite input not found: {db_path}")
    target = Path(output_dir)
    with closing(sqlite3.connect(db_path)) as connection:
        rows = connection.execute("SELECT raw_json FROM events ORDER BY event_id").fetchall()

    bronze, silver, quarantine = [], [], []
    seen = set()
    for (raw,) in rows:
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            quarantine.append({"reason": "malformed_json", "raw_record": raw})
            continue
        bronze.append(event)
        reason = _quality_check(event)
        if reason:
            quarantine.append({"event_id": event.get("event_id"), "reason": reason})
            continue
        if event["event_id"] in seen:
            continue
        seen.add(event["event_id"])
        silver.append({
            "event_id": event["event_id"],
            "tenant_id": event["tenant_id"],
            "icao24": event["payload"]["icao24"],
            "event_time": event["source_event_time"],
            "event_date": event["source_event_time"][:10],
            "latitude": event["payload"]["latitude"],
            "longitude": event["payload"]["longitude"],
            "on_ground": event["payload"].get("on_ground"),
            "velocity_mps": event["payload"].get("velocity_mps"),
            "source": event["source"]
        })

    groups = defaultdict(lambda: {"event_count": 0, "aircraft_ids": set()})
    for row in silver:
        key = (row["tenant_id"], row["event_date"])
        groups[key]["event_count"] += 1
        groups[key]["aircraft_ids"].add(row["icao24"])
    gold = [
        {"tenant_id": tenant, "event_date": date,
         "event_count": value["event_count"],
         "distinct_aircraft": len(value["aircraft_ids"])}
        for (tenant, date), value in sorted(groups.items())
    ]
    metrics = {
        "bronze_records": len(bronze),
        "silver_records": len(silver),
        "quarantined_records": len(quarantine),
        "gold_rows": len(gold),
        "storage_format": "jsonl_local_reference",
    }
    _atomic_write(target / "bronze" / "aviation_events.jsonl", _jsonlines(bronze))
    _atomic_write(target / "silver" / "aviation_states.jsonl", _jsonlines(silver))
    _atomic_write(target / "quarantine" / "invalid_records.jsonl", _jsonlines(quarantine))
    _atomic_write(target / "gold" / "daily_aircraft_summary.jsonl", _jsonlines(gold))
    _atomic_write(target / "metrics.json", json.dumps(metrics, indent=2) + "\n")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Export Phase 2A events to local Bronze/Silver/Gold layers.")
    parser.add_argument("--db", default="data/dev/aviation.sqlite3")
    parser.add_argument("--output", default="data/lakehouse")
    args = parser.parse_args()
    print(json.dumps(export_layers(args.db, args.output), indent=2))


if __name__ == "__main__":
    main()
