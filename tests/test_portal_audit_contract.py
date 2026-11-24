"""P0.2 audit storage and compose safety contract tests, no extra deps."""
import ast
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class AuditContractTests(unittest.TestCase):
    def test_audit_module_parses(self):
        code = (ROOT / "apps/api/audit_store.py").read_text(encoding="utf-8")
        functions = {n.name for n in ast.walk(ast.parse(code)) if isinstance(n, ast.FunctionDef)}
        self.assertTrue({"record_event", "recent_events", "initialize", "enabled"}.issubset(functions))
        self.assertNotIn("password", code.lower().split("def record_event")[1].split("def recent_events")[0])

    def test_sql_tenant_scoping_and_append_only_application(self):
        sql = (ROOT / "apps/api/migrations/001_audit.sql").read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS audit_events", sql)
        self.assertIn("tenant_id", sql)
        code = (ROOT / "apps/api/audit_store.py").read_text(encoding="utf-8")
        self.assertIn("WHERE tenant_id = %s", code)
        self.assertNotIn("DELETE FROM audit_events", code)

    def test_opt_in_compose_does_not_publish_postgres(self):
        base = (ROOT / "docker-compose.portal.yml").read_text(encoding="utf-8")
        extra = (ROOT / "docker-compose.portal.audit.yml").read_text(encoding="utf-8")
        self.assertNotIn("audit-db:", base)
        self.assertIn("audit-db:", extra)
        self.assertIn("condition: service_healthy", extra)
        self.assertIn("datanexus_audit_pg", extra)
        self.assertNotIn("5432:5432", extra)
        self.assertIn("portal-db.env", (ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_api_audits_login_without_echoing_password(self):
        main = (ROOT / "apps/api/main.py").read_text(encoding="utf-8")
        self.assertIn('record_event("auth_login"', main)
        self.assertIn('record_event("auth_blocked"', main)
        self.assertNotIn("record_event(\"password", main)
        self.assertIn('def audit_events(', main)

    def test_db_setup_will_not_overwrite(self):
        source = (ROOT / "scripts/create_portal_db_env.py").read_text(encoding="utf-8")
        self.assertIn('DEST.open("x"', source)
        self.assertNotIn("print(secret)", source)


if __name__ == "__main__":
    unittest.main()
