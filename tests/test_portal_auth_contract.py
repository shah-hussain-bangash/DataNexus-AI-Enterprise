"""Phase 3A.2 local auth and UI contract tests, no app dependencies required."""
import ast
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]

class AuthPortalContractTests(unittest.TestCase):
    def test_auth_source_is_parseable_and_has_session_validation(self):
        source = (ROOT / "apps/api/auth.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertTrue({"verify_token", "issue_token", "verify_password", "hash_password", "require_user"}.issubset(names))
        self.assertIn("hmac.compare_digest", source)

    def test_backend_enforces_protected_api_paths(self):
        api = (ROOT / "apps/api/main.py").read_text(encoding="utf-8")
        for name in ("events", "overview", "quality"):
            self.assertIn('def ' + name + '(', api)
        # P0.3 protects each route via require_permission(), which itself
        # depends on require_user(). Never rely on counting old route syntax.
        permissions = {
            "events": "aviation:read",
            "overview": "overview:read",
            "quality": "quality:read",
            "audit_events": "audit:read",
        }
        tree = ast.parse(api)
        for route, permission in permissions.items():
            function = next(
                node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == route
            )
            source = ast.get_source_segment(api, function)
            self.assertIn(f'Depends(require_permission("{permission}"))', source)
        policy = (ROOT / "apps/api/authorization.py").read_text(encoding="utf-8")
        self.assertIn("Depends(require_user)", policy)
        self.assertIn("if not permitted(user, permission)", policy)
        self.assertIn("tenant_id=require_tenant(user", api)
        self.assertIn("requested_tenant=tenant_id", api)

    def test_ui_has_sign_in_and_logout_routes(self):
        self.assertTrue((ROOT / "apps/web/app/sign-in/page.tsx").exists())
        self.assertTrue((ROOT / "apps/web/app/api/auth/login/route.ts").exists())
        self.assertTrue((ROOT / "apps/web/app/api/auth/logout/route.ts").exists())
        web = (ROOT / "apps/web/app/api/portal/[...path]/route.ts").read_text(encoding="utf-8")
        self.assertIn("Authorization:", web)
        self.assertIn("datanexus_session", web)

    def test_origin_matches_public_browser_address(self):
        compose = (ROOT / "docker-compose.portal.yml").read_text(encoding="utf-8")
        self.assertIn("DATANEXUS_PUBLIC_ORIGIN: http://127.0.0.1:13000", compose)
        for route in ("login", "logout"):
            code = (ROOT / f"apps/web/app/api/auth/{route}/route.ts").read_text(encoding="utf-8")
            self.assertIn("origin !== process.env.DATANEXUS_PUBLIC_ORIGIN", code)
            self.assertIn("status: 403", code)

    def test_no_committed_default_credential(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("portal.env", ignored)
        compose = (ROOT / "docker-compose.portal.yml").read_text(encoding="utf-8")
        self.assertIn("portal.env", compose)
        self.assertNotIn("DATANEXUS_SESSION_SECRET: ", compose)

if __name__ == "__main__":
    unittest.main()
