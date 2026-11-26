"""Read-only local NYC TLC data quality evidence from Phase 2.1/2.2/2.3.

The local data may not be licensed or approved. This endpoint serves only
bounded aggregate metadata. It does NOT certify source completeness or freshness.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from tlc_reporting import read_preview


def _load(path, maximum=65536):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > maximum:
        raise FileNotFoundError("Local quality evidence unavailable")
    item=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(item,dict):
        raise ValueError("Malformed local quality evidence")
    return item


def quality_evidence(data_root, now=None):
    root=Path(data_root).resolve()/"nyc_tlc"
    folder=root/"silver_gold_2024_01"
    preview=read_preview(data_root)
    validation=_load(root/"validation"/"yellow_tripdata_2024-01.parquet.validation.json")
    transform=_load(folder/"transform_manifest.json")
    expected={
        "source":"nyc_tlc_yellow_taxi",
        "file_name":"yellow_tripdata_2024-01.parquet",
        "stage":"local_validation_report_only",
        "source_sha256":preview["source_sha256"],
        "row_count":preview["validated_source_rows"],
        "required_schema_validated":True,
        "complete_row_scan":True,
    }
    if any(validation.get(key)!=value for key,value in expected.items()):
        raise ValueError("Validation evidence does not reconcile with reporting")
    if transform.get("validated_source_rows")!=preview["validated_source_rows"] or transform.get("quarantined_rows")!=preview["quarantined_rows"]:
        raise ValueError("Transformation counts do not reconcile with reporting")
    for value in (validation.get("quality_warning_counts"),transform.get("rejection_reasons")):
        if not isinstance(value,dict) or any(
            not isinstance(name,str) or type(count)!=int or count<0 for name,count in value.items()
        ):
            raise ValueError("Quality reason counters invalid")
    try:
        generated=datetime.fromisoformat(preview["generated_at_utc"].replace("Z","+00:00"))
        scanned=datetime.fromisoformat(validation["scan_completed_at_utc"].replace("Z","+00:00"))
    except (KeyError,ValueError,TypeError) as exc:
        raise ValueError("Invalid quality evidence timestamps") from exc
    if generated.tzinfo is None or scanned.tzinfo is None:
        raise ValueError("Evidence timestamps must have timezone offsets")
    clock=now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise ValueError("Monitoring clock must be timezone-aware")
    hours=(clock-generated).total_seconds()/3600
    if hours < -1/60:
        raise ValueError("Reporting timestamp is in the future")
    if scanned > clock:
        raise ValueError("Validation timestamp is in the future")
    source_count=preview["validated_source_rows"]
    silver_count=preview["silver_rows"]
    quarantine_count=preview["quarantined_rows"]
    if source_count<=0 or silver_count+quarantine_count!=source_count:
        raise ValueError("Invalid data reconciliation")
    return {
        "state":"local_quality_evidence_only",
        "source":"nyc_tlc_yellow_taxi",
        "source_month":preview["source_month"],
        "source_sha256":preview["source_sha256"],
        "validation_completed_at_utc":scanned.isoformat(),
        "report_generated_at_utc":generated.isoformat(),
        "report_age_hours":round(hours,1),
        "report_age_band":"over_168_hours" if hours>168 else "within_168_hours",
        "historical_dataset":True,
        "live_source_freshness":None,
        "source_records":source_count,
        "silver_records":silver_count,
        "quarantined_records":quarantine_count,
        "accepted_percent":round(silver_count*100/source_count,3),
        "quarantined_percent":round(quarantine_count*100/source_count,3),
        "validation_warning_counts":validation["quality_warning_counts"],
        "transformation_rejection_reasons":transform["rejection_reasons"],
        "out_of_month_trips":preview["outside_month_trip_count"],
        "reconciliation_ok":True,
        "quality_policy":"preliminary_local_rules",
        "production_approved":False,
        "caveat":"Warnings can overlap and do not equal quarantined rows. Report age is not live feed freshness. Licensing and production review pending.",
    }
