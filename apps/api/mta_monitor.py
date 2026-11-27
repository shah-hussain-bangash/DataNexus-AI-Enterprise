"""Read-only Phase 3.6 operator-generated MTA monitoring evidence."""
import json
from datetime import datetime,timezone
from pathlib import Path

def latest_monitor(data_root,now=None):
    root=Path(data_root).resolve()/"mta"/"monitor_checks"
    if not root.is_dir():raise FileNotFoundError("No MTA monitoring snapshots")
    candidates=sorted(root.glob("mta-monitor-*.json"),reverse=True)
    if not candidates:raise FileNotFoundError("No MTA monitoring snapshots")
    path=candidates[0]
    if path.is_symlink() or path.stat().st_size>16384:
        raise ValueError("Unsafe MTA monitoring evidence")
    report=json.loads(path.read_text(encoding="utf-8"))
    required={"state","checked_at_utc","topic","group","partition","low_offset",
              "high_offset_exclusive","committed_next_offset","consumer_lag_messages",
              "offset_state","stored_aggregate_records","latest_provider_timestamp_utc",
              "latest_stored_source_age_seconds","latest_stored_source_age_state",
              "source_api_checked_now","production_approved","caveat"}
    if set(report)!=required or report["state"]!="local_monitor_snapshot" or report["topic"]!="mta.subway.updates.v1" or report["group"]!="datanexus-mta-aggregate-v1" or report["partition"]!=0:
        raise ValueError("Unexpected MTA monitoring evidence")
    if report["production_approved"] is not False or report["source_api_checked_now"] is not False:
        raise ValueError("Misleading MTA monitoring status")
    for key in ("low_offset","high_offset_exclusive","stored_aggregate_records","latest_stored_source_age_seconds"):
        if type(report[key])!=int or report[key]<0:raise ValueError("Invalid monitoring metric")
    if report["low_offset"]>report["high_offset_exclusive"]:raise ValueError("Invalid offsets")
    if report["consumer_lag_messages"] is not None and (type(report["consumer_lag_messages"])!=int or report["consumer_lag_messages"]<0):
        raise ValueError("Invalid lag metric")
    if report["offset_state"] not in ("valid","unknown_uncommitted","committed_below_retention","committed_beyond_high_watermark"):
        raise ValueError("Invalid offset state")
    if (report["offset_state"]=="valid") != (report["consumer_lag_messages"] is not None):
        raise ValueError("Lag and offset state mismatch")
    clock=now or datetime.now(timezone.utc)
    stamp=datetime.fromisoformat(report["checked_at_utc"].replace("Z","+00:00"))
    if stamp.tzinfo is None or stamp>clock:raise ValueError("Monitoring snapshot timestamp invalid")
    age=int((clock-stamp).total_seconds())
    # Never present a stale snapshot as a current Kafka status.
    return {**report,"snapshot_age_seconds":age,"snapshot_stale":age>300,
            "live_kafka_health_verified_now":False}
