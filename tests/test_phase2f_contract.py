"""Dependency-free checks for S3 storage prototype wiring."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Phase2FContractTests(unittest.TestCase):
    def test_s3_job_parseable(self):
        p = ROOT / "pipelines/spark_iceberg_s3.py"
        tree = ast.parse(p.read_text(encoding="utf-8"))
        functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertTrue({"run", "main"}.issubset(functions))

    def test_development_rest_and_object_store_are_separate(self):
        text = (ROOT / "docker-compose.minio.yml").read_text(encoding="utf-8")
        for token in ("minio:", "s3-init:", "iceberg-rest:", "iceberg-s3:",
                      "iceberg-aws-bundle:1.9.2", "phase2f_minio_data",
                      "127.0.0.1:19001:9001"):
            self.assertIn(token, text)

    def test_gitignore_secrets(self):
        self.assertIn("phase2f.env", (ROOT / ".gitignore").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
