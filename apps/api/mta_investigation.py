"""Compose a bounded read-only MTA incident brief from local evidence."""

from datetime import datetime
import hashlib
import json

from mta_alert_history import read_alert_history
from mta_incident_review import records
from mta_recovery_evidence import latest_recovery


def investigate(data_root, assessment_sha256=None):
    history = read_alert_history(data_root, limit=50)
    candidates = [
        entry for entry in history["entries"]
        if entry["alert_count"] and (
            assessment_sha256 is None or entry["snapshot_sha256"] == assessment_sha256
        )
    ]
    assessment = max(
        candidates, key=lambda entry: datetime.fromisoformat(entry["assessed_at_utc"]),
        default=None,
    )
    if assessment is None and assessment_sha256 is not None:
        return None

    result = {
        "status": "review_required" if assessment else "insufficient_evidence",
        "assessment": None,
        "review": None,
        "recovery": None,
        "citations": [],
        "gaps": [],
        "actions_performed": [],
    }
    if assessment is None:
        result["gaps"].append("no_actionable_assessment_in_read_window")
    else:
        digest = assessment["snapshot_sha256"]
        result["assessment"] = {
            "snapshot_sha256": digest,
            "assessed_at_utc": assessment["assessed_at_utc"],
            "source_snapshot_checked_at_utc": assessment["source_snapshot_checked_at_utc"],
            "severity": assessment["status"],
            "alerts": [
                {"code": alert["code"], "severity": alert["severity"]}
                for alert in assessment["alerts"]
            ],
        }
        result["citations"].append({
            "id": "assessment",
            "endpoint": "/api/v1/mta/alert-history",
            "reference": digest,
            "observed_utc": assessment["assessed_at_utc"],
        })

        actions = records(data_root, digest)
        last = actions[-1] if actions else None
        state = ("unreviewed", "acknowledged", "assigned", "resolved")[len(actions)]
        result["review"] = {
            "state": state,
            "record_count": len(actions),
            "last_action_utc": last["recorded_at_utc"] if last else None,
            "resolution_self_reported": state == "resolved",
        }
        if last:
            fingerprint = hashlib.sha256(
                json.dumps(last, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            result["citations"].append({
                "id": "review",
                "endpoint": "/api/v1/mta/incident-reviews",
                "reference": digest,
                "entry_sha256": fingerprint,
                "sequence": len(actions),
                "observed_utc": last["recorded_at_utc"],
            })
        result["gaps"].append(
            "resolution_requires_independent_verification" if state == "resolved"
            else "operator_review_incomplete"
        )

    recovery = latest_recovery(data_root)["report"]
    if recovery is None:
        result["gaps"].append("no_verified_local_restore_report")
    else:
        result["recovery"] = {
            "checked_at_utc": recovery["checked_at_utc"],
            "report_stale": recovery["report_stale"],
            "records_restored": recovery["restored_records"],
            "isolated_restore_verified": recovery["isolated_restore_verified"],
        }
        result["citations"].append({
            "id": "recovery_context",
            "endpoint": "/api/v1/mta/recovery",
            "reference": recovery["backup_file_sha256"],
            "observed_utc": recovery["checked_at_utc"],
        })
        if recovery["report_stale"]:
            result["gaps"].append("local_restore_report_is_stale")

    result["gaps"].extend(["live_provider_health_unverified", "case_specific_kafka_recovery_unverified"])
    return result
