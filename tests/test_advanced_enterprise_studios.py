"""UI-only enterprise studio regression checks: no fake backend actions."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AdvancedStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "apps/web/app/workspaces/page.tsx").read_text(encoding="utf-8")
        cls.studio = (ROOT / "apps/web/app/workspaces/advanced-enterprise.tsx").read_text(encoding="utf-8")
        cls.styles = (ROOT / "apps/web/app/workspaces/advanced-enterprise.css").read_text(encoding="utf-8")

    def test_all_four_studios_have_navigation_and_render_paths(self):
        for route, mode in (
            ("powerbi-studio", "powerbi"),
            ("ai-studio", "ai"),
            ("security-studio", "security"),
            ("operations-studio", "ops"),
        ):
            self.assertIn('["'+route+'"', self.page)
            self.assertIn('<AdvancedEnterprise mode="'+mode+'"', self.page)

    def test_enterprise_studios_cover_required_ui_journeys(self):
        for label in (
            "Report canvas", "Semantic model", "Refresh & governance",
            "Grounded GenAI assistant", "Model registry", "Investigation agent",
            "Human approvals", "Identity & RBAC", "Data governance",
            "Threat controls", "Release gate", "Recovery",
            "Data freshness", "No approved observation connected",
        ):
            if label == "Data freshness":
                self.assertIn("Source freshness scoring", self.studio)
            else:
                self.assertIn(label, self.studio)

    def test_production_actions_are_not_connected_to_real_services(self):
        for label in (
            "Publish to Power BI — unavailable",
            "Start real investigation — unavailable",
            "Execute — unavailable",
            "No answer generated",
            "does not authorize, approve, or execute any backend action",
            "Release gate remains BLOCKED (0/16 approved)",
        ):
            self.assertIn(label, self.studio)
        self.assertNotIn('fetch(', self.studio)

    def test_responsive_accessible_design(self):
        self.assertIn('@media(max-width:680px)', self.styles)
        self.assertIn(':focus-visible', self.styles)
        self.assertIn('aria-label=', self.studio)
