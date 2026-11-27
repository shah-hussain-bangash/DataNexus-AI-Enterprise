"""No-network EIA v2 hourly demand connector safety and Power BI contracts."""
import io,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import ingest_eia_energy as eia
def fixture():
 return {"response":{"total":"1","data":[{
     "period":"2024-01-02T12","respondent":"US48","type":"D",
     "value":"450000","value-units":"megawatthours"}]}}
class Response:
 def __init__(self,b):self.data=io.BytesIO(b)
 def __enter__(self):return self
 def __exit__(self,*args):self.data.close()
 def read(self,n):return self.data.read(n)
class EnergyTests(unittest.TestCase):
 def test_bounded_public_query_no_key(self):
  url=eia.public_url("2024-01-01","2024-01-07")
  self.assertIn("electricity/rto/region-data/data/",url)
  self.assertNotIn("api_key",url)
  self.assertIn("facets%5Btype%5D%5B%5D=D",url)
  with self.assertRaises(ValueError):eia.public_url("2024-01-01","2024-01-20")
 def test_missing_key_fails_before_network(self):
  with tempfile.TemporaryDirectory() as p:
   with self.assertRaises(ValueError):eia.fetch("2024-01-01","2024-01-07",folder=Path(p),key="")
 def test_normalize_hourly_energy(self):
  rows=eia.normalize(fixture(),"2024-01-01","2024-01-07")
  self.assertEqual(rows[0]["demand_mwh"],450000)
 def test_reject_incomplete_page(self):
  bad=fixture();bad["response"]["total"]="4"
  with self.assertRaises(ValueError):eia.normalize(bad,"2024-01-01","2024-01-07")
 def test_reject_wrong_type_or_units(self):
  bad=fixture();bad["response"]["data"][0]["type"]="NG"
  with self.assertRaises(ValueError):eia.normalize(bad,"2024-01-01","2024-01-07")
  bad=fixture();bad["response"]["data"][0]["value-units"]="MW"
  with self.assertRaises(ValueError):eia.normalize(bad,"2024-01-01","2024-01-07")
 def test_provenance_and_tamper(self):
  with tempfile.TemporaryDirectory() as p:
   f=Path(p);raw=json.dumps(fixture()).encode()
   result=eia.fetch("2024-01-01","2024-01-07",folder=f,
      opener=lambda req,timeout:Response(raw),key="test-secret-key")
   self.assertEqual(result["rows"],1)
   manifest=Path(result["manifest"]).read_text()
   self.assertNotIn("test-secret-key",manifest)
   self.assertEqual(len(eia.load(f)["records"]),1)
   with self.assertRaises(FileExistsError):eia.fetch("2024-01-01","2024-01-07",folder=f,key="test-secret-key")
   snapshot=next(x for x in f.glob("eia-us48-hourly-demand-*.json") if ".manifest." not in x.name)
   snapshot.write_text("[]")
   with self.assertRaises(ValueError):eia.load(f)
 def test_powerbi_contract(self):
  exporter=(ROOT/"dashboards/powerbi/Update_DataNexus_Overview.py").read_text()
  model=(ROOT/"dashboards/powerbi/DataNexus_EndToEnd.SemanticModel/definition/model.tmdl").read_text()
  self.assertIn("'energy_hourly':energy_rows",exporter)
  self.assertIn("ref table EnergyHourly",model)
