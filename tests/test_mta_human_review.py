"""Exercise durable approval binding and the local two-identity API boundary."""
from concurrent.futures import ThreadPoolExecutor
from importlib import util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from apps.api import mta_human_review as review


ASSESSMENT = "a" * 64
BRIEF = {"status": "review_required", "assessment": {"snapshot_sha256": ASSESSMENT}, "gaps": ["unverified"]}


class ApprovalStorageTests(unittest.TestCase):
    def test_submission_retries_and_only_one_concurrent_decision(self):
        with tempfile.TemporaryDirectory() as data:
            request = review.submit(data, "demo", "operator", BRIEF, now=10)
            self.assertEqual(request, review.submit(data, "demo", "operator", BRIEF, now=11))
            self.assertIsNone(review.get(data, "other", request["request_id"], now=12))

            def decide(choice):
                try:
                    return review.decide(data, "demo", "reviewer", request["request_id"],
                                         choice, request["evidence_sha256"], BRIEF, now=20)
                except review.ReviewConflict:
                    return None

            with ThreadPoolExecutor(max_workers=2) as pool:
                first, second = pool.map(decide, ["approve", "reject"])
            self.assertEqual((first is None) + (second is None), 1)
            accepted = first or second
            self.assertEqual(decide(accepted["decision"]["choice"]), accepted)
            self.assertEqual(review.get(data, "demo", request["request_id"], now=25), accepted)

    def test_self_review_expiry_and_changed_evidence_are_rejected(self):
        with tempfile.TemporaryDirectory() as data:
            request = review.submit(data, "demo", "Operator", BRIEF, now=100)
            target = request["request_id"]
            digest = request["evidence_sha256"]
            with self.assertRaises(review.SelfReview):
                review.decide(data, "demo", "operator", target, "approve", digest, BRIEF, now=110)
            with self.assertRaisesRegex(review.ReviewConflict, "digest"):
                review.decide(data, "demo", "reviewer", target, "approve", "f" * 64, BRIEF, now=110)
            with self.assertRaisesRegex(review.ReviewConflict, "changed"):
                review.decide(data, "demo", "reviewer", target, "approve", digest,
                              {**BRIEF, "gaps": ["changed"]}, now=110)
            with self.assertRaisesRegex(review.ReviewConflict, "expired"):
                review.decide(data, "demo", "reviewer", target, "approve", digest,
                              BRIEF, now=100 + review.TTL_SECONDS)
            self.assertEqual(review.get(data, "demo", target, now=110)["status"], "pending")


@unittest.skipUnless(util.find_spec("fastapi") and util.find_spec("httpx"), "requires FastAPI and httpx")
class ApprovalApiTests(unittest.TestCase):
    def test_signed_distinct_roles_and_evidence_binding(self):
        from fastapi.testclient import TestClient

        api = Path(__file__).resolve().parents[1] / "apps" / "api"
        with patch.object(sys, "path", [str(api), *sys.path]):
            spec = util.spec_from_file_location("mta_approval_test_main", api / "main.py")
            portal = util.module_from_spec(spec)
            spec.loader.exec_module(portal)
            from auth import hash_password

        admin_password = "operator-test-password"
        reviewer_password = "reviewer-test-password"
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {
            "DATANEXUS_DATA_ROOT": root, "DATANEXUS_SESSION_SECRET": "s" * 64,
            "DATANEXUS_ADMIN_USERNAME": "operator_test", "DATANEXUS_ADMIN_PASSWORD_HASH": hash_password(admin_password),
            "DATANEXUS_MTA_REVIEWER_USERNAME": "reviewer_test",
            "DATANEXUS_MTA_REVIEWER_PASSWORD_HASH": hash_password(reviewer_password),
            "DATANEXUS_ADMIN_TENANT": "demo", "DATANEXUS_AUDIT_REQUIRED": "false",
        }), TestClient(portal.app) as client, patch.object(portal, "investigate", return_value=BRIEF) as evidence:
            def login(username, password):
                result = client.post("/auth/login", json={"username": username, "password": password})
                self.assertEqual(result.status_code, 200)
                return {"Authorization": "Bearer " + result.json()["access_token"]}

            operator = login("operator_test", admin_password)
            reviewer = login("reviewer_test", reviewer_password)
            self.assertEqual(client.get("/auth/me", headers=reviewer).json()["role"], "mta_reviewer")
            root_path = "/api/v1/mta/review-requests"
            body = {"assessment_sha256": ASSESSMENT}
            self.assertEqual(client.post(root_path, json=body).status_code, 401)
            self.assertEqual(client.post(root_path, json=body, headers=reviewer).status_code, 403)
            self.assertEqual(client.get("/api/v1/mta/investigation", headers=reviewer).status_code, 403)
            response = client.post(root_path, json=body, headers=operator)
            self.assertEqual(response.status_code, 200)
            request = response.json()
            target = root_path + "/" + request["request_id"]
            self.assertEqual(client.get(target, headers=reviewer).json(), request)
            decision = {"decision": "approve", "evidence_sha256": request["evidence_sha256"]}
            self.assertEqual(client.post(target + "/decision", json=decision, headers=operator).status_code, 403)
            evidence.return_value = {**BRIEF, "gaps": ["new evidence"]}
            self.assertEqual(client.post(target + "/decision", json=decision, headers=reviewer).status_code, 409)
            evidence.return_value = BRIEF
            result = client.post(target + "/decision", json=decision, headers=reviewer)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["status"], "approved")
            self.assertEqual(result.json()["decision"]["by"], "reviewer_test")
            self.assertEqual(client.post(target + "/decision", json=decision, headers=reviewer).json(), result.json())


if __name__ == "__main__":
    unittest.main()
