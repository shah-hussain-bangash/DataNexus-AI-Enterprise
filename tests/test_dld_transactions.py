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
 def test_real_dld_export_schema_and_exact_duplicate(self):
  header="TRANSACTION_NUMBER,INSTANCE_DATE,GROUP_EN,PROCEDURE_EN,AREA_EN,PROP_TYPE_EN,TRANS_VALUE,TOTAL_BUYER\n"
  rows=("X1,2026-11-01 12:00:00,Sales,Sale,Business Bay,Unit,1250000,1\n"
        "X1,2026-11-01 12:00:00,Sales,Sale,Business Bay,Unit,1250000,1\n"
        "X2,2026-11-01 13:00:00,Sales,Sell - Pre registration,Business Bay,Unit,2000000,2\n")
  data,counts=dld.summarize_actual_export(io.StringIO(header+rows))
  self.assertEqual(counts["source_rows"],3)
  self.assertEqual(counts["skipped_exact_duplicates"],1)
  self.assertEqual(counts["sales_rows"],2)
  self.assertEqual({x["procedure"] for x in data},{"Sale","Sell - Pre registration"})
  self.assertNotIn("X1",json.dumps(data))
 def test_real_dld_conflicting_duplicate_rejected(self):
  csv=("TRANSACTION_NUMBER,INSTANCE_DATE,GROUP_EN,PROCEDURE_EN,AREA_EN,PROP_TYPE_EN,TRANS_VALUE\n"
    "X1,2026-11-01 12:00:00,Sales,Sale,A,Unit,10000\n"
    "X1,2026-11-01 12:00:00,Sales,Sale,A,Unit,90000\n")
  with self.assertRaises(ValueError):dld.summarize_actual_export(io.StringIO(csv))
 def test_real_dld_manifest_roundtrip(self):
  csv=("TRANSACTION_NUMBER,INSTANCE_DATE,GROUP_EN,PROCEDURE_EN,AREA_EN,PROP_TYPE_EN,TRANS_VALUE\n"
    "X1,2026-11-01 12:00:00,Sales,Sale,A,Unit,10000\n"
    "X2,2026-11-01 13:00:00,Sales,Sell - Pre registration,B,Land,90000\n")
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);source=p/"transactions.csv";source.write_text(csv)
   result=dld.ingest(source,p/"out")
   self.assertEqual(result["sales_rows"],2)
   self.assertEqual(len(dld.load(p/"out")["records"]),2)
 def test_powerbi_contract(self):
  s=(ROOT/"dashboards/powerbi/Update_DataNexus_Overview.py").read_text()
  m=(ROOT/"dashboards/powerbi/DataNexus_EndToEnd.SemanticModel/definition/model.tmdl").read_text()
  self.assertIn("'property_daily':property_rows",s)
  self.assertIn("ref table PropertyDaily",m)
