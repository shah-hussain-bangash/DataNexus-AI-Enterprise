"""Pure audit rule checks without a Spark installation."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Phase2GAuditTests(unittest.TestCase):
    def test_script_has_read_only_audit_entrypoint(self):
        source = (ROOT / "pipelines/spark_iceberg_audit.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        self.assertTrue({"run", "evaluate_metrics", "main"}.issubset(names))
        self.assertIn(".snapshots", source)
        self.assertIn("exceptAll", source)
        self.assertNotIn("createOrReplace()", source)
        self.assertNotIn(".writeTo(", source)

    def test_audit_compose_reuses_existing_volume(self):
        source = (ROOT / "docker-compose.audit.yml").read_text(encoding="utf-8")
        self.assertIn("phase2f_ivy_cache:/root/.ivy2", source)
        self.assertIn("iceberg-audit:", source)
        self.assertIn("spark_iceberg_audit.py", source)

    def test_metric_rules_report_mismatches(self):
        source = (ROOT / "pipelines/spark_iceberg_audit.py").read_text(encoding="utf-8")
        # Execute only the pure function, without importing Spark.
        tree = ast.parse(source)
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate_metrics")
        scope = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "<audit-rules>", "exec"), scope)
        metrics = {
            "silver_rows": 2, "duplicate_event_ids": 0, "null_silver_keys": 0,
            "gold_mismatched_rows": 0,
            "snapshot_counts": {"silver": 1, "gold": 1, "quarantine": 1},
        }
        self.assertEqual([], scope["evaluate_metrics"](metrics, 2))
        metrics["duplicate_event_ids"] = 1
        self.assertTrue(scope["evaluate_metrics"](metrics, 2))
        metrics["duplicate_event_ids"] = 0
        metrics["gold_mismatched_rows"] = 1
        self.assertTrue(scope["evaluate_metrics"](metrics, 2))


if __name__ == "__main__":
    unittest.main()
