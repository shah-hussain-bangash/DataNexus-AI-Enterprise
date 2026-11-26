"""DataNexus browser acceptance tests (run separately; requires a running local portal).

Install: python -m pip install playwright && python -m playwright install chromium
Run: python -m unittest discover -s tests/browser -p 'test_*.py' -v
Override: DATANEXUS_BASE_URL=http://127.0.0.1:13000
"""
import os
import unittest
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

BASE = os.environ.get("DATANEXUS_BASE_URL", "http://127.0.0.1:13000").rstrip("/")
ARTIFACTS = Path(os.environ.get("DATANEXUS_BROWSER_ARTIFACTS", "data/dev/browser-acceptance"))
WORKSPACES = "/workspaces"


@unittest.skipUnless(sync_playwright is not None, "Install Playwright: python -m pip install playwright")
class BrowserAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))

    def tearDown(self):
        if self.errors or getattr(self, "_outcome", None) and not self._test_passed():
            ARTIFACTS.mkdir(parents=True, exist_ok=True)
            try:
                self.page.screenshot(path=str(ARTIFACTS / (self._testMethodName + ".png")), full_page=True)
            except Exception:
                pass
        try:
            self.assertEqual(self.errors, [], "Uncaught client-side JS exception(s)")
        finally:
            self.context.close()

    def _test_passed(self):
        outcome = self._outcome
        return not any(test is self and exc is not None for test, exc in (outcome.result.failures + outcome.result.errors))

    def open(self, view, domain="mobility"):
        response = self.page.goto(
            BASE + WORKSPACES + "?domain=" + domain + "&view=" + view,
            wait_until="domcontentloaded", timeout=30000
        )
        self.assertIsNotNone(response, "No response: is your local Docker portal running?")
        self.assertEqual(response.status, 200, "The workspace route is not reachable")
        self.page.locator(".nx-shell").wait_for(timeout=15000)
        return self.page

    def test_01_all_seven_domain_navigation(self):
        for domain in ("mobility", "weather", "seismic", "coastal", "river", "property", "energy"):
            self.open("historical", domain)
            self.assertIn("view=historical", self.page.url)
            self.assertIn("domain=" + domain, self.page.url)
            self.page.get_by_text("Historical Big Data", exact=False).first.wait_for()

    def test_02_72_capability_studio_search_and_tabs(self):
        page = self.open("capabilities")
        page.get_by_text("CAPABILITY 01 / 72", exact=False).first.wait_for()
        page.get_by_role("tab", name="Workflow").first.click()
        page.get_by_role("tab", name="Acceptance").first.click()
        self.assertIn("view=capabilities", page.url)
        self.assertTrue(page.get_by_text("CONCEPT UI", exact=False).count() >= 1)

    def test_03_76_task_roadmap_search_filters_and_status(self):
        page = self.open("implementation")
        page.get_by_role("heading", name="76 implementation and verification tasks").wait_for()
        self.assertIn("76/76", page.locator(".ir-kpis").inner_text())
        page.get_by_role("textbox", name="Search the 76 implementation tasks").fill("security penetration")
        page.get_by_text("Security penetration testing").first.wait_for()
        page.get_by_role("textbox", name="Search the 76 implementation tasks").fill("")
        page.get_by_role("combobox", name="Filter by workstream").select_option(label="Generative AI")
        self.assertIn("6 tasks match", page.locator(".ir-list-heading").inner_text())
        self.assertIn("No production verification", page.locator(".ir-detail").inner_text())

    def test_04_ux_enhancement_navigation_and_keyboard_command(self):
        page = self.open("experience")
        page.get_by_role("heading", name="Dashboard experience studio").wait_for()
        page.locator(".ex-menu").get_by_role("button", name="Notification center").click()
        self.assertIn("Preview notification inbox", page.locator(".ex-main").inner_text())
        page.keyboard.press("Control+k")
        page.get_by_role("dialog", name="Dashboard command palette").wait_for()
        page.get_by_role("textbox", name="Search dashboard destinations").fill("Security")
        self.assertTrue(page.get_by_role("button", name="Security Center").count() >= 1)
        page.keyboard.press("Escape")
        self.assertEqual(page.get_by_role("dialog", name="Dashboard command palette").count(), 0)

    def test_05_studio_routes_are_not_presented_as_live(self):
        for view in ("powerbi-studio", "ai-studio", "security-studio", "operations-studio"):
            page = self.open(view)
            self.assertIn("DESIGN FIXTURES ONLY", page.locator(".nx-warning").inner_text())
            self.assertIn("view=" + view, page.url)

    def test_06_mobile_menu_and_reflow(self):
        self.context.close()
        self.context = self.browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        page = self.open("implementation")
        page.get_by_role("button", name="Open menu").click()
        self.assertIn("open", page.locator(".nx-sidebar").get_attribute("class"))
        page.get_by_role("button", name="Close navigation menu").click()
        self.assertNotIn("open", page.locator(".nx-sidebar").get_attribute("class"))
        self.assertTrue(page.get_by_role("heading", name="76 implementation and verification tasks").is_visible())


if __name__ == "__main__":
    unittest.main()
