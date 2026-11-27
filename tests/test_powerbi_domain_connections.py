"""DataNexus Power BI domain evidence export contract tests."""
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DASH=ROOT/"dashboards/powerbi"
class PowerBIDomainContracts(unittest.TestCase):
 def test_exporter_reports_contracts_without_claiming_connections(self):
  content=(DASH/"Update_DataNexus_Overview.py").read_text(encoding="utf-8")
  self.assertIn("domain_coverage",content)
  self.assertIn("'Continuous Live Verified':False",content)
  self.assertIn("'Connection State':'not_connected'",content)
  self.assertIn("'Historical Connection':'Not connected'",content)
  self.assertNotIn("requests.get(",content)
 def test_domain_model_imports_actual_local_inventory(self):
  content=(DASH/"DataNexus_EndToEnd.SemanticModel/definition/tables/DomainCoverage.tmdl").read_text(encoding="utf-8")
  self.assertIn("Inventory[domain_coverage]",content)
  self.assertIn("DomainCoverage",content)
  self.assertIn("ExpectedIds",content)
 def test_aviation_daily_only_uses_local_data(self):
  content=(DASH/"DataNexus_EndToEnd.SemanticModel/definition/tables/AviationDaily.tmdl").read_text(encoding="utf-8")
  self.assertIn("Inventory[aviation_daily]",content)
  self.assertNotIn("Web.Contents",content)
 def test_model_has_new_refs(self):
  model=(DASH/"DataNexus_EndToEnd.SemanticModel/definition/model.tmdl").read_text(encoding="utf-8")
  self.assertIn("ref table DomainCoverage",model)
  self.assertIn("ref table AviationDaily",model)
