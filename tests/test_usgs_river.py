"""USGS modern daily-river API no-network validation and Power BI contracts."""
import io,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import ingest_usgs_river as river
def fixture():
 return {"type":"FeatureCollection","numberMatched":1,"numberReturned":1,"links":[],
         "features":[{"type":"Feature","id":"test-only","properties":{
           "monitoring_location_id":river.SITE,"parameter_code":"00060",
           "statistic_id":"00003","time":"2024-01-02","value":"123.0",
           "unit_of_measure":"ft3/s","approval_status":"Approved"}}]}
class Response:
 def __init__(self,raw):self.raw=io.BytesIO(raw)
 def __enter__(self):return self
 def __exit__(self,*args):self.raw.close()
 def read(self,n):return self.raw.read(n)
class RiverTests(unittest.TestCase):
 def test_modern_api_and_bounded_date_window(self):
  self.assertIn("api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items",river.url_for("2024-01-01","2024-01-07"))
  self.assertIn("parameter_code=00060",river.url_for("2024-01-01","2024-01-07"))
  with self.assertRaises(ValueError):river.url_for("2024-01-01","2024-03-01")
 def test_normalize_measurements(self):
  rows=river.normalize(fixture(),"2024-01-01","2024-01-07")
  self.assertEqual(rows[0]["mean_discharge_cfs"],123)
 def test_wrong_site_rejected(self):
  obj=fixture();obj["features"][0]["properties"]["monitoring_location_id"]="OTHER"
  with self.assertRaises(ValueError):river.normalize(obj,"2024-01-01","2024-01-07")
 def test_missing_units_rejected(self):
  obj=fixture();del obj["features"][0]["properties"]["unit_of_measure"]
  with self.assertRaises(ValueError):river.normalize(obj,"2024-01-01","2024-01-07")
 def test_pagination_rejected(self):
  obj=fixture();obj["numberMatched"]=2
  with self.assertRaises(ValueError):river.normalize(obj,"2024-01-01","2024-01-07")
 def test_no_overwrite_and_tamper(self):
  with tempfile.TemporaryDirectory() as t:
   folder=Path(t);raw=json.dumps(fixture()).encode()
   out=river.fetch("2024-01-01","2024-01-07",folder=folder,opener=lambda req,timeout:Response(raw))
   self.assertEqual(out["records"],1)
   self.assertEqual(len(river.load(folder)["records"]),1)
   with self.assertRaises(FileExistsError):river.fetch("2024-01-01","2024-01-07",folder=folder)
   snap=next(x for x in folder.glob("river-daily-*.json") if ".manifest." not in x.name)
   snap.write_text("[]")
   with self.assertRaises(ValueError):river.load(folder)
 def test_powerbi_contract(self):
  exporter=(ROOT/"dashboards/powerbi/Update_DataNexus_Overview.py").read_text()
  model=(ROOT/"dashboards/powerbi/DataNexus_EndToEnd.SemanticModel/definition/model.tmdl").read_text()
  self.assertIn("'river_daily':river_rows",exporter)
  self.assertIn("ref table RiverDaily",model)
