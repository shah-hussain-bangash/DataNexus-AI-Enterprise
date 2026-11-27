"""No-network NOAA CO-OPS hourly-height and Power BI contracts."""
import io,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import ingest_noaa_coastal as coastal
def fixture():
 return {"metadata":{"id":"8518750","name":"The Battery"},"data":[{"t":"2024-01-01 00:00","v":"1.321"},{"t":"2024-01-01 01:00","v":"1.200"}]}
class Response:
 def __init__(self,raw):self.io=io.BytesIO(raw)
 def __enter__(self):return self
 def __exit__(self,*args):self.io.close()
 def read(self,n):return self.io.read(n)
class CoastalTests(unittest.TestCase):
 def test_official_fixed_station_url_and_window(self):
  url=coastal.url_for("2024-01-01","2024-01-07")
  self.assertIn("station=8518750",url)
  self.assertIn("product=hourly_height",url)
  self.assertIn("time_zone=gmt",url)
  with self.assertRaises(ValueError):coastal.url_for("2024-01-01","2024-03-01")
 def test_normalizes_verified_hourly(self):
  rows=coastal.normalize(fixture(),"2024-01-01","2024-01-07")
  self.assertEqual(len(rows),2)
  self.assertEqual(rows[0]["datum"],"MLLW")
 def test_reject_duplicate_and_bad_station(self):
  bad=fixture();bad["data"].append(bad["data"][0])
  with self.assertRaises(ValueError):coastal.normalize(bad,"2024-01-01","2024-01-07")
  bad=fixture();bad["metadata"]["id"]="OTHER"
  with self.assertRaises(ValueError):coastal.normalize(bad,"2024-01-01","2024-01-07")
 def test_reject_invalid_water_levels(self):
  bad=fixture();bad["data"][0]["v"]="NaN"
  with self.assertRaises(ValueError):coastal.normalize(bad,"2024-01-01","2024-01-07")
 def test_writes_and_revalidates_without_network(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d);raw=json.dumps(fixture()).encode()
   result=coastal.fetch("2024-01-01","2024-01-07",folder=folder,opener=lambda req,timeout:Response(raw))
   self.assertEqual(result["records"],2)
   self.assertEqual(len(coastal.load(folder)["records"]),2)
   with self.assertRaises(FileExistsError):coastal.fetch("2024-01-01","2024-01-07",folder=folder)
 def test_detects_snapshot_tampering(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d);raw=json.dumps(fixture()).encode()
   coastal.fetch("2024-01-01","2024-01-07",folder=folder,opener=lambda req,timeout:Response(raw))
   snapshot=next(p for p in folder.glob("coastal-hourly-*.json") if ".manifest." not in p.name)
   rows=json.loads(snapshot.read_text());rows[0]["height_m"]=9.0
   snapshot.write_text(json.dumps(rows))
   with self.assertRaises(ValueError):coastal.load(folder)
 def test_powerbi_connection_contract(self):
  overview=(ROOT/"dashboards/powerbi/Update_DataNexus_Overview.py").read_text()
  model=(ROOT/"dashboards/powerbi/DataNexus_EndToEnd.SemanticModel/definition/model.tmdl").read_text()
  self.assertIn("'coastal_hourly':coastal_rows",overview)
  self.assertIn("ref table CoastalHourly",model)
