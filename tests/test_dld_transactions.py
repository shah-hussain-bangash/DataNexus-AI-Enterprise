"""Offline Dubai Land Department operator supplied CSV contract tests."""
import io,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import ingest_dld_transactions as dld

HEADER="Transaction Number,Transaction Date,Transaction Type,Area,Property Type,Amount,No. of Buyer\n"
ROWS="A1,2024-01-02,Sale,Business Bay,Unit,2500000,2\nA2,2024-01-02,Sales,Business Bay,Unit,1500000,1\nA3,2024-01-03,Mortgage,Business Bay,Unit,4000000,1\n"

class DLDContracts(unittest.TestCase):
 def test_sale_aggregation_excludes_mortgages_and_identifiers(self):
  rows,counts=dld.summarize(io.StringIO(HEADER+ROWS))
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]["sales_count"],2)
  self.assertEqual(rows[0]["total_amount_aed"],4000000)
  self.assertEqual(counts["excluded_non_sales"],1)
  self.assertNotIn("A1",json.dumps(rows))
  self.assertNotIn("Buyer",json.dumps(rows))
 def test_fail_closed_duplicate_ids(self):
  with self.assertRaises(ValueError):dld.summarize(io.StringIO(HEADER+ROWS+ROWS.splitlines()[0]+"\n"))
 def test_fail_closed_wrong_schema(self):
  with self.assertRaises(ValueError):dld.summarize(io.StringIO("date,value\n2024-01-02,4\n"))
 def test_invalid_amount(self):
  with self.assertRaises(ValueError):dld.summarize(io.StringIO(HEADER+ROWS.replace("2500000","NaN")))
 def test_no_sales_rejected(self):
  with self.assertRaises(ValueError):dld.summarize(io.StringIO(HEADER+"A3,2024-01-03,Mortgage,Business Bay,Unit,4000000,1\n"))
 def test_manifest_and_tamper(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp);source=folder/"dld.csv";source.write_text(HEADER+ROWS,encoding="utf-8")
   out=folder/"out";result=dld.ingest(source,out)
   self.assertEqual(result["sales_rows"],2)
   content=(out/(dld.STEM+".manifest.json")).read_text()
   self.assertIn('"license_approved": false',content)
   self.assertNotIn("A1",content)
   self.assertEqual(dld.load(out)["records"][0]["sales_count"],2)
   (out/(dld.STEM+".json")).write_text("[]")
   with self.assertRaises(ValueError):dld.load(out)
 def test_powerbi_contract(self):
  s=(ROOT/"dashboards/powerbi/Update_DataNexus_Overview.py").read_text()
  m=(ROOT/"dashboards/powerbi/DataNexus_EndToEnd.SemanticModel/definition/model.tmdl").read_text()
  self.assertIn("'property_daily':property_rows",s)
  self.assertIn("ref table PropertyDaily",m)
