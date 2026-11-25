"""Comprehensive enterprise UI experience design contracts."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ExperienceDesignContracts(unittest.TestCase):
 def test_complete_ui_navigation(self):
  page=(ROOT/"apps/web/app/workspaces/page.tsx").read_text(encoding="utf-8")
  for term in ("Overview","Source Explorer","Data Catalog","Alerts & Incidents","Settings","Historical Analytics","Live Operations","Station Detail","Data Health","Power BI"):
   self.assertIn(term,page)
 def test_ui_journeys(self):
  studio=(ROOT/"apps/web/app/workspaces/studio.tsx").read_text(encoding="utf-8")
  for term in ("One platform. Every source.","Source & provenance","Incident response journey","Workspace Preferences","Not connected","NOT REAL SOURCE DATA","Copy page link","Export UI review","Saved only"):
   self.assertIn(term,studio)
 def test_existing_aviation_and_property_preserved(self):
  page=(ROOT/"apps/web/app/page.tsx").read_text(encoding="utf-8")
  assert "/api/portal/events" in page
  assert "/api/portal/overview" in page
  assert (ROOT/"apps/web/app/dubai-property/page.tsx").is_file()
