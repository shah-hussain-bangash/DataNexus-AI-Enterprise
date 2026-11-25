"""Complete 72-function UI studio selection and coverage source contracts."""
import re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CapabilityDesignTests(unittest.TestCase):
 def test_every_requirements_group_and_all_72_items(self):
  s=(ROOT/"apps/web/app/workspaces/capability-data.ts").read_text(encoding="utf-8")
  indexes=[int(v) for v in re.findall(r'"id": (\d+)',s)]
  self.assertEqual(indexes,list(range(1,73)))
  for group in ["Dashboard UI/UX","Domain integrations","Historical big data","Streaming data","Power BI","ML/GenAI/Agents","Security/governance","Production/reliability"]:
   self.assertIn(group,s)
 def test_navigation_and_all_states(self):
  page=(ROOT/"apps/web/app/workspaces/page.tsx").read_text(encoding="utf-8")
  design=(ROOT/"apps/web/app/workspaces/capability-studio.tsx").read_text(encoding="utf-8")
  self.assertIn('["capabilities","All Capabilities"',page)
  self.assertIn('<CapabilityStudio/>',page)
  for label in ["Design","Workflow","Acceptance","DATA UNAVAILABLE","CONCEPT UI","Not verified","Search capabilities","Human approval","Production operations"]:
   self.assertIn(label,design)
 def test_responsive_accessibility(self):
  css=(ROOT/"apps/web/app/workspaces/capability-studio.css").read_text(encoding="utf-8")
  for needle in ["@media(max-width:950px)","@media(max-width:570px)",":focus-visible"]:
   self.assertIn(needle,css)
