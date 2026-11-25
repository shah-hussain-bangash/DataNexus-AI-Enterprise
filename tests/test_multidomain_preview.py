"""New multi-domain UI contract."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PreviewTests(unittest.TestCase):
 def test_domain_views(self):
  page=(ROOT/"apps/web/app/workspaces/page.tsx").read_text(encoding="utf-8")
  for word in ("Urban Mobility","Weather & Climate","Seismic Activity","Coastal Water Levels","River & Watershed","Dubai Property","Energy Grid","DESIGN FIXTURES ONLY","Historical Analytics","Live Operations","Station Detail","Data Health","Power BI"):
   self.assertIn(word,page)
 def test_report_pages(self):
  page=(ROOT/"apps/web/app/workspaces/page.tsx").read_text(encoding="utf-8")
  for word in ("Executive Overview","Mobility Explorer","Feed Health","Power BI Build"):
   self.assertIn(word,page)
