"""UI refresh contract: visual changes must preserve functional routes."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class PortalVisualRefreshTests(unittest.TestCase):
    def test_command_center_content_and_real_data_bindings(self):
        code = (ROOT / "apps/web/app/page.tsx").read_text(encoding="utf-8")
        for term in ("Mission control for", "hero-radar-rings", "hero-satellite", "overview?.workspace?.tenant_id", "/api/portal/overview", "/api/portal/events", "signOut", "EventTable"):
            self.assertIn(term, code)
    def test_sign_in_form_remains_functional(self):
        code = (ROOT / "apps/web/app/sign-in/page.tsx").read_text(encoding="utf-8")
        for term in ("signin-console", "/api/auth/login", "onSubmit={submit}", "type={visible ? \"text\" : \"password\"}", "Enter the workspace"):
            self.assertIn(term, code)
    def test_sign_in_has_attributed_aviation_photography(self):
        page = (ROOT / "apps/web/app/sign-in/page.tsx").read_text(encoding="utf-8")
        styles = (ROOT / "apps/web/app/sign-in/sign-in.css").read_text(encoding="utf-8")
        self.assertIn("signin-photo-gallery", page)
        self.assertIn("signin-photo-backdrop", page)
        self.assertIn("No airline affiliation", page)
        self.assertIn("commons.wikimedia.org/wiki/Special:FilePath/", styles)
        self.assertIn("signin-photo-aircraft", styles)
        self.assertIn("signin-photo-airport", styles)
        self.assertIn("@media(max-width:880px)", styles)

    def test_refresh_responsive_styles(self):
        css = (ROOT / "apps/web/app/globals.css").read_text(encoding="utf-8")
        sign = (ROOT / "apps/web/app/sign-in/sign-in.css").read_text(encoding="utf-8")
        self.assertIn(".hero-radar-rings", css)
        self.assertIn(".hero-secondary", css)
        self.assertIn("@media(max-width:590px)", css)
        self.assertIn(".signin-console", sign)
        self.assertIn("@media(max-width:880px)", sign)
if __name__ == "__main__":
    unittest.main()
