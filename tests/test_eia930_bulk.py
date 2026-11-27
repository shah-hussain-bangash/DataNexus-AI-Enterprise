"""Offline EIA-930 bulk CSV importer tests."""
import io,sys,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import ingest_eia930_bulk as bulk
HEADER="Balancing Authority,UTC Time at End of Hour,Demand (MW),Region\n"
def fake_csv():
 from datetime import datetime,timedelta
 start=datetime(2024,1,1,0)
 return HEADER+''.join(f"PJM,{(start+timedelta(hours=i)).strftime('%m/%d/%Y %I:%M:%S %p')},32000,Mid-Atlantic\\n".replace('\\n','\n') for i in range(48))
class EIA930BulkTests(unittest.TestCase):
 def test_parse_bounded_pjm_week(self):
  rows=bulk.parse_rows(io.StringIO(fake_csv()))
  self.assertEqual(len(rows),48)
  self.assertEqual(rows[0]["respondent"],"PJM")
  self.assertEqual(rows[0]["demand_mwh"],32000)
 def test_unknown_header_rejected(self):
  with self.assertRaises(ValueError):bulk.parse_rows(io.StringIO("date,power\n"))
 def test_duplicate_rejected(self):
  csv=fake_csv()+fake_csv().splitlines()[1]+"\n"
  with self.assertRaises(ValueError):bulk.parse_rows(io.StringIO(csv))
 def test_missing_demand_not_zero(self):
  csv=fake_csv().replace("32000,Mid-Atlantic","NA,Mid-Atlantic",1)
  self.assertEqual(len(bulk.parse_rows(io.StringIO(csv))),47)
 def test_immutable_hash_manifest_and_tamper(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/bulk.FILENAME;source.write_text(fake_csv(),encoding="utf-8")
   out=root/"out"
   result=bulk.import_csv(source,out)
   self.assertEqual(result["records"],48)
   self.assertEqual(len(bulk.load(out)["records"]),48)
   with self.assertRaises(FileExistsError):bulk.import_csv(source,out)
   manifest=(out/(bulk.STEM+".manifest.json")).read_text()
   self.assertNotIn("api_key",manifest)
   (out/(bulk.STEM+".json")).write_text("[]")
   with self.assertRaises(ValueError):bulk.load(out)
 def test_reject_incorrect_filename(self):
  with tempfile.TemporaryDirectory() as p:
   wrong=Path(p)/"incorrect.csv";wrong.write_text(fake_csv())
   with self.assertRaises(ValueError):bulk.import_csv(wrong,Path(p)/"out")
 def test_powerbi_exporter_recognizes_bulk(self):
  s=(ROOT/"dashboards/powerbi/Update_DataNexus_Overview.py").read_text()
  self.assertIn("eia_bulk.load",s)
  self.assertIn("EIA-930 six-month BALANCE CSV",s)
