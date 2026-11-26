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


    def test_07_original_aviation_and_property_routes(self):
        for route in ("/", "/dubai-property"):
            response = self.page.goto(BASE + route, wait_until="domcontentloaded", timeout=30000)
            self.assertIsNotNone(response)
            self.assertEqual(response.status, 200)
            self.page.locator("main").first.wait_for(timeout=15000)
            if route == "/" and "/sign-in" in self.page.url:
                self.assertTrue(self.page.get_by_role("heading", name="Sign in to DataNexus").is_visible(), "Unauthenticated aviation route should redirect to sign-in")
            self.assertTrue(self.page.locator("main").count() >= 1, route + " needs a main landmark")
            self.assertGreater(len(self.page.locator("body").inner_text().strip()), 80)

    def test_08_palette_focus_trap_and_restoration(self):
        page = self.open("experience")
        trigger = page.locator(".ex-actionbar button").first
        trigger.focus()
        trigger.click()
        dialog = page.get_by_role("dialog", name="Dashboard command palette")
        dialog.wait_for()
        search = dialog.get_by_role("textbox", name="Search dashboard destinations")
        self.assertTrue(search.evaluate("(el) => document.activeElement === el"))
        last = dialog.locator(".ex-command-results button").last
        last.focus()
        page.keyboard.press("Tab")
        self.assertTrue(search.evaluate("(el) => document.activeElement === el"), "Tab should wrap to first command palette control")
        page.keyboard.press("Shift+Tab")
        self.assertTrue(last.evaluate("(el) => document.activeElement === el"), "Shift+Tab should wrap back to final control")
        page.keyboard.press("Escape")
        self.assertEqual(dialog.count(), 0)
        self.assertTrue(trigger.evaluate("(el) => document.activeElement === el"), "Focus must return to opening control")

    def test_09_mobile_horizontal_reflow_of_roadmap_and_studios(self):
        self.context.close()
        self.context = self.browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        for view in ("implementation", "capabilities", "experience", "powerbi-studio", "ai-studio", "security-studio", "operations-studio"):
            page = self.open(view)
            page.locator(".nx-main").wait_for()
            overflow = page.evaluate("() => ({width: document.documentElement.clientWidth, content: document.documentElement.scrollWidth})")
            self.assertLessEqual(overflow["content"], overflow["width"] + 2,
                                 view + " has horizontal document overflow at 390px: " + str(overflow))


    def test_10_real_reporting_explorer_filters_with_mocked_authenticated_response(self):
        """Browser test explicitly uses synthetic API fixture, not actual user records."""
        import json
        fake={
            "tenant_id":"browser-test-tenant","source_month":"2024-01",
            "source_sha256":"a"*64,"validated_source_rows":14,
            "silver_rows":12,"quarantined_rows":2,
            "in_month_trip_count":10,"outside_month_trip_count":2,
            "in_month_days":2,"outside_month_days":1,
            "daily":[
                {"date":"2024-01-01","trip_count":4,"trip_distance_sum":6,"total_amount_sum":50,"within_source_month":True},
                {"date":"2024-01-02","trip_count":6,"trip_distance_sum":8,"total_amount_sum":70,"within_source_month":True},
                {"date":"2024-02-01","trip_count":2,"trip_distance_sum":3,"total_amount_sum":20,"within_source_month":False},
            ],"caveat":"SYNTHETIC BROWSER TEST DATA ONLY"
        }
        self.page.route("**/api/portal/nyc-tlc/reporting",lambda route:route.fulfill(status=200,content_type="application/json",body=json.dumps(fake)))
        page=self.open("historical")
        explorer=page.locator(".tlc-explorer")
        explorer.wait_for(timeout=15000)
        self.assertIn("10",explorer.locator(".tlc-kpis").inner_text())
        self.assertEqual(explorer.locator(".tlc-table tbody tr").count(),2)
        explorer.get_by_label("Historical from date").fill("2024-01-02")
        self.assertEqual(explorer.locator(".tlc-table tbody tr").count(),1)
        self.assertIn("6",explorer.locator(".tlc-kpis").inner_text())
        explorer.get_by_label("Historical metric").select_option("total_amount_sum")
        self.assertIn("trip total",explorer.locator(".tlc-chart").get_attribute("aria-label").lower())
        explorer.get_by_role("button",name="Reset filters").click()
        explorer.get_by_label("Include outside-month dates").check()
        explorer.get_by_label("Historical to date").fill("2024-02-02")
        self.assertEqual(explorer.locator(".tlc-table tbody tr").count(),3)
        self.assertIn("Outside January",explorer.locator(".tlc-table").inner_text())
        self.assertIn("12",explorer.locator(".tlc-kpis").inner_text())

    def test_11_historical_reporting_no_session_shows_unavailable(self):
        page=self.open("historical")
        panel=page.locator('[aria-label="Local NYC TLC Gold reporting"]')
        panel.wait_for(timeout=15000)
        page.get_by_text("Sign in to access historical reporting.").wait_for(timeout=15000)
        self.assertEqual(panel.locator(".tlc-explorer").count(),0)

if __name__ == "__main__":
    unittest.main()
