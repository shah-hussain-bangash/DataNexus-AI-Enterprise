"""Source metadata must remain tenant-scoped, auditable and fail closed."""
import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load_registry():
 spec=importlib.util.spec_from_file_location("dn_source_registry",ROOT/"apps/api/source_registry.py")
 module=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(module)
 return module

class RegistryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.registry=load_registry()
 def test_contracts_cover_seven_domains_without_fake_data(self):
  data=self.registry.catalog("tenant-a")
  self.assertEqual(len(data["sources"]),7)
  self.assertEqual({d["id"] for d in data["sources"]},{"mobility","weather","seismic","coastal","river","property","energy"})
  for s in data["sources"]:
   self.assertEqual(s["historical_state"],"not_connected")
   self.assertEqual(s["latest_state"],"not_connected")
   self.assertIsNone(s["verified_rows"])
   self.assertIsNone(s["approved_snapshot"])
 def test_catalog_is_a_copy(self):
  result=self.registry.catalog("tenant-a")
  result["sources"][0]["name"]="tampered"
  self.assertNotEqual(self.registry.catalog("tenant-a")["sources"][0]["name"],"tampered")
 def test_empty_tenant_fails_closed(self):
  with self.assertRaises(ValueError):self.registry.catalog(" ")
  with self.assertRaises(ValueError):self.registry.readiness("")
 def test_readiness_requires_sixteen_external_approvals(self):
  state=self.registry.readiness("tenant-a")
  self.assertEqual(state["release_status"],"blocked")
  self.assertEqual(state["approved_controls"],0)
  self.assertEqual(state["required_controls"],16)
  self.assertEqual(len(state["controls"]),16)
 def test_endpoints_require_permissions_and_tenant(self):
  main=(ROOT/"apps/api/main.py").read_text(encoding="utf-8")
  policy=(ROOT/"apps/api/authorization.py").read_text(encoding="utf-8")
  proxy=(ROOT/"apps/web/app/api/portal/[...path]/route.ts").read_text(encoding="utf-8")
  self.assertIn('require_permission("catalog:read")',main)
  self.assertIn('require_permission("readiness:read")',main)
  self.assertIn("require_tenant(user)",main)
  self.assertIn('"catalog:read"',policy)
  self.assertIn('"readiness:read"',policy)
  self.assertIn('"catalog", "readiness"',proxy)
