"""76-task roadmap coverage: counts, navigation, and no false production approvals."""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ImplementationRoadmapTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=(ROOT/"apps/web/app/workspaces/implementation-roadmap-data.ts").read_text(encoding="utf-8")
  cls.ui=(ROOT/"apps/web/app/workspaces/implementation-roadmap.tsx").read_text(encoding="utf-8")
  cls.page=(ROOT/"apps/web/app/workspaces/page.tsx").read_text(encoding="utf-8")
  cls.css=(ROOT/"apps/web/app/workspaces/implementation-roadmap.css").read_text(encoding="utf-8")

 def test_76_contiguous_tasks_and_all_ten_workstreams(self):
  ids=[int(v) for v in re.findall(r'"id": (\d+)',self.data)]
  self.assertEqual(ids,list(range(1,77)))
  for group,count in [
   ("UI/UX and Dashboard",7),("Real Data Integrations",8),("Historical Big Data",7),
   ("Live Streaming",7),("Power BI",7),("Machine Learning",7),
   ("Generative AI",6),("Agentic AI",6),("Enterprise Security and Governance",9),("Production Engineering",12),
  ]:
   self.assertIn('"name": "'+group+'"',self.data)
  self.assertIn("Security penetration testing",self.data)
  self.assertIn("Approval of all 16 production release controls",self.data)

 def test_preserve_existing_register_and_aviation_property(self):
  self.assertIn('["implementation","76-Task Roadmap"',self.page)
  self.assertIn('<ImplementationRoadmap/>',self.page)
  self.assertIn('["capabilities","All Capabilities"',self.page)
  self.assertIn('Existing Aviation',self.page)
  self.assertIn('Dubai Property UI',self.page)
  old=(ROOT/"apps/web/app/workspaces/capability-data.ts").read_text(encoding="utf-8")
  self.assertEqual(len(re.findall(r'"id": (\d+)',old)),72)

 def test_real_status_not_inferred_from_review_notes(self):
  for part in ("ROADMAP ONLY","No production verification","0/16","Not verified",
               "not submitted to GitHub","pending independent verification",
               "browser session only","No approval is inferred"):
   if part=="not submitted to GitHub":
    self.assertIn("Not submitted to GitHub",self.ui)
   else:
    self.assertIn(part,self.ui)
  self.assertNotIn("fetch(",self.ui)
  self.assertNotIn("localStorage",self.ui)

 def test_search_filters_and_mobile(self):
  for part in ("Filter by workstream","Search the 76 implementation tasks",
               "Filter local review notes","Copy 76-task register","aria-label="):
   self.assertIn(part,self.ui)
  self.assertIn('@media(max-width:1040px)',self.css)
  self.assertIn('@media(max-width:650px)',self.css)
  self.assertIn(':focus-visible',self.css)
