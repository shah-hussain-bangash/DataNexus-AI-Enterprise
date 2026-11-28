"""Verify that incident briefs keep historical evidence and recovery claims separate."""
from copy import deepcopy
from importlib import util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


API = Path(__file__).resolve().parents[1] / "apps" / "api"


def load_module(name, filename):
    with patch.object(sys, "path", [str(API), *sys.path]):
        spec = util.spec_from_file_location(name, API / filename)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


investigator = load_module("test_mta_investigation_impl", "mta_investigation.py")
DIGEST = "a" * 64
BACKUP = "b" * 64
STAMP = "2026-11-27T10:00:00+00:00"


def alert(digest=DIGEST, stamp=STAMP):
    return {
        "snapshot_sha256": digest, "assessed_at_utc": stamp, "source_snapshot_checked_at_utc": stamp,
        "status": "attention", "alert_count": 1, "alerts": [
            {"code": "STORED_OBSERVATION_OLD", "severity": "warning", "reason": "untrusted alert text"},
        ],
    }


class MtaInvestigationTests(unittest.TestCase):
    @patch.object(investigator, "latest_recovery")
    @patch.object(investigator, "records")
    @patch.object(investigator, "read_alert_history")
    def test_operator_assertion_and_restore_evidence_do_not_establish_recovery(self, history, records, recovery):
        history.return_value = {"entries": [alert()]}
        records.return_value = [{"recorded_at_utc": STAMP, "note": "private operator note"}] * 3
        recovery.return_value = {"report": {
            "checked_at_utc": STAMP, "report_stale": True, "restored_records": 7,
            "isolated_restore_verified": True, "backup_file_sha256": BACKUP,
        }}

        result = investigator.investigate("data")
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["review"]["state"], "resolved")
        self.assertTrue(result["review"]["resolution_self_reported"])
        self.assertEqual(result["recovery"]["records_restored"], 7)
        self.assertEqual(result["actions_performed"], [])
        self.assertIn("resolution_requires_independent_verification", result["gaps"])
        self.assertIn("local_restore_report_is_stale", result["gaps"])
        self.assertIn("case_specific_kafka_recovery_unverified", result["gaps"])
        self.assertEqual([cite["id"] for cite in result["citations"]], ["assessment", "review", "recovery_context"])
        self.assertEqual(result["citations"][1]["reference"], DIGEST)
        self.assertRegex(result["citations"][1]["entry_sha256"], r"^[a-f0-9]{64}$")
        self.assertNotIn("private operator", str(result))
        self.assertNotIn("untrusted alert", str(result))
        history.assert_called_once_with("data", limit=50)
        records.assert_called_once_with("data", DIGEST)

    @patch.object(investigator, "latest_recovery", return_value={"report": None})
    @patch.object(investigator, "records", return_value=[])
    @patch.object(investigator, "read_alert_history")
    def test_newest_actionable_default_and_explicit_selection(self, history, records, recovery):
        older = alert("c" * 64, "2026-11-26T10:00:00+00:00")
        newer = alert()
        clear = {**deepcopy(newer), "snapshot_sha256": "d" * 64,
                 "assessed_at_utc": "2026-11-28T10:00:00+00:00", "alert_count": 0}
        history.return_value = {"entries": [older, clear, newer]}
        self.assertEqual(investigator.investigate("data")["assessment"]["snapshot_sha256"], DIGEST)
        self.assertEqual(investigator.investigate("data", "c" * 64)["assessment"]["snapshot_sha256"], "c" * 64)
        self.assertIsNone(investigator.investigate("data", "d" * 64))
        self.assertIsNone(investigator.investigate("data", "e" * 64))

    @patch.object(investigator, "latest_recovery", return_value={"report": None})
    @patch.object(investigator, "read_alert_history", return_value={"entries": []})
    def test_missing_evidence_is_explicit(self, history, recovery):
        result = investigator.investigate("data")
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["citations"], [])
        self.assertIn("no_actionable_assessment_in_read_window", result["gaps"])
        self.assertIn("no_verified_local_restore_report", result["gaps"])


@unittest.skipUnless(util.find_spec("fastapi") and util.find_spec("httpx"), "requires FastAPI and httpx")
class MtaInvestigationApiTests(unittest.TestCase):
    def test_sign_in_query_validation_and_unavailable_evidence(self):
        from fastapi.testclient import TestClient

        portal = load_module("test_mta_investigation_portal_main", "main.py")
        from auth import issue_token
        secret = "x" * 64
        with patch.dict(os.environ, {
            "DATANEXUS_SESSION_SECRET": secret, "DATANEXUS_ADMIN_USERNAME": "unit_admin",
            "DATANEXUS_ADMIN_PASSWORD_HASH": "unused-in-token-tests", "DATANEXUS_ADMIN_TENANT": "demo",
            "DATANEXUS_AUDIT_REQUIRED": "false",
        }), TestClient(portal.app) as client:
            headers = {"Authorization": "Bearer " + issue_token("unit_admin", "admin", "demo", secret.encode())}
            endpoint = "/api/v1/mta/investigation"
            with patch.object(portal, "investigate", return_value=None) as run:
                self.assertEqual(client.get(endpoint).status_code, 401)
                self.assertEqual(client.get(endpoint, params={"assessment_sha256": "invalid"}, headers=headers).status_code, 422)
                run.assert_not_called()
                self.assertEqual(client.get(endpoint, params={"assessment_sha256": DIGEST}, headers=headers).status_code, 404)
            with patch.object(portal, "investigate", side_effect=ValueError("sensitive invalid artifact detail")):
                response = client.get(endpoint, headers=headers)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json(), {"detail": "Local MTA investigation evidence unavailable"})


if __name__ == "__main__":
    unittest.main()
