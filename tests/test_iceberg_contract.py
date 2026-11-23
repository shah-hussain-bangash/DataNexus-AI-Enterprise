"""Basic dependency-free contract checks for the Phase 2E prototype."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class IcebergContractTests(unittest.TestCase):
    def test_module_is_parseable_and_has_transform(self):
        path = ROOT / "pipelines/spark_iceberg_medallion.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        self.assertTrue({"transform", "run", "main"}.issubset(names))

    def test_iceberg_catalog_and_tables_declared(self):
        source = (ROOT / "pipelines/spark_iceberg_medallion.py").read_text(encoding="utf-8")
        for token in ("IcebergSparkSessionExtensions", "silver_aviation",
                      "quarantined_aviation", "gold_daily_aircraft",
                      'createOrReplace()', '"event_id"'):
            self.assertIn(token, source)

    def test_compose_has_local_warehouse_mount(self):
        source = (ROOT / "docker-compose.iceberg.yml").read_text(encoding="utf-8")
        self.assertIn("./data:/opt/project/data", source)
        self.assertIn("iceberg-spark-runtime-3.5_2.12:1.9.2", source)


if __name__ == "__main__":
    unittest.main()
