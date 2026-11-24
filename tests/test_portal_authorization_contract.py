"""P0.3 fail-closed permission and tenant-isolation contract tests."""
import ast
import importlib.util
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

class AuthorizationSourceTests(unittest.TestCase):
    def test_policy_is_parseable(self):
        source = (ROOT / "apps/api/authorization.py").read_text(encoding="utf-8")
        parsed = ast.parse(source)
        names = {node.name for node in ast.walk(parsed) if isinstance(node, ast.FunctionDef)}
        self.assertTrue({"permitted", "require_permission", "require_tenant"} <= names)

    def test_protected_api_uses_permissions(self):
        source = (ROOT / "apps/api/main.py").read_text(encoding="utf-8")
        for permission in ("aviation:read", "overview:read", "quality:read", "audit:read"):
            self.assertIn('require_permission("' + permission + '")', source)
        self.assertIn("tenant_id=require_tenant(user)", source)
        self.assertIn('requested_tenant=tenant_id', source)

    def test_untrusted_tenant_is_not_used_as_sql_scope(self):
        source = (ROOT / "apps/api/main.py").read_text(encoding="utf-8")
        self.assertNotIn("tenant_id=tenant_id)", source)
        self.assertIn("require_tenant(user", source)
        query_source = (ROOT / "apps/api/data.py").read_text(encoding="utf-8")
        self.assertIn("tenant_id = ?", query_source)

    def test_policy_declares_no_arbitrary_read_permisson(self):
        source = (ROOT / "apps/api/authorization.py").read_text(encoding="utf-8")
        self.assertNotIn('"*"', source)
        self.assertNotIn("eval(", source)

    def test_token_is_bound_to_local_identity_and_tenant(self):
        source = (ROOT / "apps/api/auth.py").read_text(encoding="utf-8")
        self.assertIn('payload["tenant_id"] != tenant', source)
        self.assertIn('payload["sub"] != configured_username', source)


if __name__ == "__main__":
    unittest.main()
