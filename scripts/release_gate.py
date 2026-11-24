"""Evidence-based production release gate for DataNexus AI Enterprise.

This gate does not deploy anything. It deliberately fails closed until every
critical control has approved external verification evidence. Evidence alone
does not prove security; release owners must review underlying test artifacts.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "production-evidence"
CONTROL_IDS = (
    "identity_sso_mfa",
    "authorization_tenant_isolation",
    "data_ingestion_resilience",
    "stream_processing_recovery",
    "lakehouse_integrity",
    "api_security_and_rate_limits",
    "ml_model_evaluation",
    "genai_grounding_and_safety",
    "agent_approval_audit",
    "observability_and_alerting",
    "secrets_supply_chain",
    "disaster_recovery",
    "load_and_performance",
    "deployment_rollbacks",
    "data_licensing_and_privacy",
    "end_to_end_acceptance",
)
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def check_control(control_id, evidence_dir=EVIDENCE_DIR):
    """Return a fail-closed result, never infer that a control is implemented."""
    if control_id not in CONTROL_IDS:
        raise ValueError("Unknown control")
    path = Path(evidence_dir) / (control_id + ".json")
    base = {"control": control_id, "verified": False, "reason": "No approved evidence"}
    if not path.is_file():
        return base
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or record.get("control") != control_id:
            raise ValueError("Evidence control mismatch")
        if record.get("result") != "pass":
            raise ValueError("Control has not passed")
        if record.get("environment") != "production":
            raise ValueError("Verification must target production")
        if not isinstance(record.get("approved_by"), str) or not record["approved_by"].strip():
            raise ValueError("Missing release approver")
        if not isinstance(record.get("artifact_sha256"), str) or not SHA256.fullmatch(record["artifact_sha256"]):
            raise ValueError("Missing SHA-256 evidence integrity reference")
        raw = record.get("verified_at")
        if not isinstance(raw, str):
            raise ValueError("Missing verification timestamp")
        tested = datetime.strptime(raw, TIME_FORMAT).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if tested > now:
            raise ValueError("Future-dated verification")
        if (now - tested).total_seconds() > 30 * 24 * 3600:
            raise ValueError("Evidence older than 30 days")
        return {"control": control_id, "verified": True, "reason": "Approved evidence recorded (manual artifact review still required)"}
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return {"control": control_id, "verified": False, "reason": "Invalid evidence: " + str(exc)}


def readiness_report(evidence_dir=EVIDENCE_DIR):
    controls = [check_control(key, evidence_dir) for key in CONTROL_IDS]
    passed = sum(item["verified"] for item in controls)
    return {
        "project": "DataNexus AI Enterprise",
        "environment": "production",
        "status": "READY_FOR_MANUAL_RELEASE_REVIEW" if passed == len(controls) else "BLOCKED",
        "passed": passed,
        "required": len(controls),
        "controls": controls,
        "disclaimer": "This gate verifies evidence metadata only; independent review of underlying artifacts is mandatory.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fail-closed DataNexus production evidence gate")
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE_DIR)
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args(argv)
    report = readiness_report(arguments.evidence_dir)
    if arguments.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"DataNexus production release: {report['status']} ({report['passed']}/{report['required']})")
        for control in report["controls"]:
            state = "PASS" if control["verified"] else "BLOCK"
            print(f"  [{state}] {control['control']}: {control['reason']}")
        print(report["disclaimer"])
    return 0 if report["status"] == "READY_FOR_MANUAL_RELEASE_REVIEW" else 1


if __name__ == "__main__":
    sys.exit(main())
