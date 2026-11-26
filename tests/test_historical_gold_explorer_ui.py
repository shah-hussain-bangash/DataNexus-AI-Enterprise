"""Phase 2.4 historical interactive client uses only authenticated real reporting rows."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class HistoricalExplorerContracts(unittest.TestCase):
 def test_real_source_driven_controls_and_no_fake_values(self):
  content=(ROOT/"apps/web/app/workspaces/historical-gold-explorer.tsx").read_text(encoding="utf-8")
  for value in ('daily:GoldDay[]','Historical metric','Historical from date','Historical to date','Include outside-month dates','Reset filters','aria-label="Interactive real historical Gold analytics"','filtered.reduce','within_source_month','No real Gold records','not live or production approved'):
   self.assertIn(value,content)
  self.assertNotIn('Math.random',content)
  self.assertNotIn('fetch(',content)
 def test_actual_backend_evidence_used(self):
  evidence=(ROOT/"apps/web/app/workspaces/backend-evidence.tsx").read_text(encoding="utf-8")
  page=(ROOT/"apps/web/app/workspaces/page.tsx").read_text(encoding="utf-8")
  self.assertIn('HistoricalGoldExplorer daily={gold.data.daily} sourceMonth={gold.data.source_month}',evidence)
  self.assertIn('import "./historical-gold-explorer.css";',page)
 def test_responsive_and_accessible_chart(self):
  css=(ROOT/"apps/web/app/workspaces/historical-gold-explorer.css").read_text(encoding="utf-8")
  self.assertIn('overflow:auto',css)
  self.assertIn('max-width:520px',css)
  chart=(ROOT/"apps/web/app/workspaces/historical-gold-explorer.tsx").read_text(encoding="utf-8")
  self.assertIn('role="img"',chart)
  self.assertIn('<table',chart)
  self.assertIn('scope="col"',chart)
