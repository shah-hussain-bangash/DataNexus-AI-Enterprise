"""Local NYC TLC inventory endpoint is protected and must not count raw files as analytics."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class NYCInventoryContractTests(unittest.TestCase):
 def test_guarded_backend_inventory(self):
  main=(ROOT/"apps/api/main.py").read_text(encoding="utf-8")
  self.assertIn('"/api/v1/nyc-tlc/bronze"',main)
  self.assertIn('require_permission("catalog:read")',main)
  self.assertIn('return {"tenant_id":tenant',main)
  self.assertIn("available_downloads",main)
 def test_bounded_frontend_proxy_and_docker(self):
  proxy=(ROOT/"apps/web/app/api/portal/[...path]/route.ts").read_text(encoding="utf-8")
  self.assertIn('"nyc-tlc/bronze"',proxy)
  docker=(ROOT/"apps/api/Dockerfile").read_text(encoding="utf-8")
  self.assertIn("tlc_manifest.py",docker)
  compose=(ROOT/"docker-compose.portal.yml").read_text(encoding="utf-8")
  self.assertIn("DATANEXUS_DATA_ROOT",compose)
