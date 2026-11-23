"""Fast contract tests for Phase 2D module without requiring PySpark."""
import ast
import unittest
from pathlib import Path


PATH = Path(__file__).resolve().parents[1] / "pipelines/spark_kafka_stream.py"


class SparkStreamContractTests(unittest.TestCase):
    def test_source_uses_kafka_and_checkpoint(self):
        tree = ast.parse(PATH.read_text(encoding="utf-8"))
        names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertIn("run", names)
        self.assertIn("validate_args", names)
        text = PATH.read_text(encoding="utf-8")
        for required in ('readStream.format("kafka")', '"checkpointLocation"', 'availableNow=True', '"kafka_offset"', '"quality_reason"'):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
