"""Production release gate must fail closed in an unverified environment."""
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_gate", ROOT / "scripts/release_gate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProductionReleaseGateTests(unittest.TestCase):
    def test_missing_evidence_blocks_every_control(self):
        with tempfile.TemporaryDirectory() as directory:
            report = module.readiness_report(directory)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(report["passed"], 0)
            self.assertGreaterEqual(report["required"], 15)
            self.assertEqual(module.main(["--evidence-dir", directory]), 1)

    def test_self_claimed_pass_without_approval_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            name = module.CONTROL_IDS[0]
            Path(directory, name + ".json").write_text(json.dumps({
                "control": name,
                "result": "pass",
                "environment": "production",
            }), encoding="utf-8")
            self.assertFalse(module.check_control(name, directory)["verified"])

    def test_expired_and_future_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            name = module.CONTROL_IDS[0]
            item = {"control": name, "result": "pass", "environment": "production",
                    "approved_by": "independent-reviewer",
                    "artifact_sha256": "a" * 64, "verified_at": "2020-01-01T00:00:00Z"}
            path = Path(directory, name + ".json")
            path.write_text(json.dumps(item), encoding="utf-8")
            self.assertFalse(module.check_control(name, directory)["verified"])
            item["verified_at"] = "2099-01-01T00:00:00Z"
            path.write_text(json.dumps(item), encoding="utf-8")
            self.assertFalse(module.check_control(name, directory)["verified"])

    def test_approved_metadata_needs_all_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            name = module.CONTROL_IDS[0]
            item = {"control": name, "result": "pass", "environment": "production",
                    "approved_by": "independent-reviewer",
                    "artifact_sha256": "a" * 64,
                    "verified_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
            Path(directory, name + ".json").write_text(json.dumps(item), encoding="utf-8")
            report = module.readiness_report(directory)
            self.assertEqual(report["passed"], 1)
            self.assertEqual(report["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
