"""Dashboard UI enhancements are present, navigable, and explicitly non-production."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ExperienceExtensionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.page=(ROOT/"apps/web/app/workspaces/page.tsx").read_text(encoding="utf-8")
  cls.code=(ROOT/"apps/web/app/workspaces/experience-extensions.tsx").read_text(encoding="utf-8")
  cls.css=(ROOT/"apps/web/app/workspaces/experience-extensions.css").read_text(encoding="utf-8")

 def test_dashboard_navigation_and_deep_links(self):
  self.assertIn('["experience","UX Enhancements"',self.page)
  self.assertIn('<ExperienceExtensions domain={domain}',self.page)
  self.assertIn('|"experience";',self.page)
  self.assertIn('mode==="experience"?"Dashboard Experience"',self.page)

 def test_nine_requested_ux_extensions_present(self):
  for value in ("Workspace layout","Notification center","Design system","Cross-filter studio","Lineage explorer","User administration","Guided onboarding","Context help","Accessibility lab"):
   self.assertIn(value,self.code)
  self.assertIn("Command palette",self.code)
  self.assertIn('event.key.toLowerCase()==="k"',self.code)
  self.assertIn('setCommandOpen(false)',self.code)

 def test_controls_are_local_and_no_permission_or_prod_calls(self):
  for value in ("datanexus.layout.preview.v1","window.localStorage","Not connected","No actual lineage graph","Create user — unavailable","Unverified","no production workflows"):
   if value=="No actual lineage graph":
    self.assertIn("No actual lineage graph is connected",self.code)
   else:
    self.assertIn(value,self.code)
  self.assertNotIn("fetch(",self.code)
  self.assertNotIn("navigator.sendBeacon(",self.code)

 def test_responsive_and_accessibility_restrictions(self):
  self.assertIn('@media(max-width:650px)',self.css)
  self.assertIn('@media(prefers-reduced-motion:reduce)',self.css)
  self.assertIn(':focus-visible',self.css)
  for value in ('aria-modal="true"','aria-label="Dashboard command palette"','aria-label="Experience enhancements"'):
   self.assertIn(value,self.code)
