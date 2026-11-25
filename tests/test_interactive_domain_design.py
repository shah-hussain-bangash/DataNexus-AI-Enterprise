"""UI interaction milestone source contract; validate complete route build separately."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class InteractiveDesignTests(unittest.TestCase):
 def test_interactive_chart_map_and_table(self):
  code=(ROOT/"apps/web/app/workspaces/finishing.tsx").read_text(encoding="utf-8")
  for term in ("Geographic Explorer","onStationChange","Next chart position","Previous chart position","Data Table & Drillthrough","rowsPage","finish-modal","No fixture rows","FIXTURES ONLY"):
   self.assertIn(term,code)
 def test_state_previews_and_safe_export(self):
  code=(ROOT/"apps/web/app/workspaces/finishing.tsx").read_text(encoding="utf-8")
  for term in ('"loading"','"empty"','"error"','"stale"','"unauthorized"',"exportDisabled=true","Simulated service error"):
   self.assertIn(term,code)
 def test_url_filters_and_responsive(self):
  page=(ROOT/"apps/web/app/workspaces/page.tsx").read_text(encoding="utf-8")
  css=(ROOT/"apps/web/app/workspaces/finishing.css").read_text(encoding="utf-8")
  for name in ('updateQuery("region"','updateQuery("period"','FinishingExperience','setPreviewState','Station C','Station D'):
   self.assertIn(name,page)
  for name in ("@media(max-width:1050px)","@media(max-width:590px)","prefers-reduced-motion","focus"):
   self.assertIn(name,css if name!="focus" else page+css)
 def test_existing_aviation_and_signin_preserved(self):
  avi=(ROOT/"apps/web/app/page.tsx").read_text(encoding="utf-8")
  signin=(ROOT/"apps/web/app/sign-in/page.tsx").read_text(encoding="utf-8")
  self.assertIn("/api/portal/events",avi)
  self.assertIn("/api/auth/login",signin)
