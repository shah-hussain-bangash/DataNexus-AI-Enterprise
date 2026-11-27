"""No-network USGS connector contract."""
import io,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import ingest_usgs_seismic as u
def sample():
 return {"type":"FeatureCollection","metadata":{"count":1},"features":[{"type":"Feature","id":"example","properties":{"time":1704067200000,"mag":5.2,"place":"test only"},"geometry":{"type":"Point","coordinates":[65.0,25.0,10.0]}}]}
class Response:
 def __init__(self,content):self.fd=io.BytesIO(content)
 def __enter__(self):return self
 def __exit__(self,*args):self.fd.close()
 def read(self,n):return self.fd.read(n)
class UsgsConnectorTests(unittest.TestCase):
 def test_window_bounded(self):
  with self.assertRaises(ValueError):u.query("2024-01-01","2024-04-01")
 def test_duplicate_event_rejected(self):
  x=sample();x["features"].append(x["features"][0]);x["metadata"]["count"]=2
  with self.assertRaises(ValueError):u.normalize(x,"2024-01-01","2024-02-01")
 def test_truncation_rejected(self):
  x=sample();x["metadata"]["count"]=5000
  with self.assertRaises(ValueError):u.normalize(x,"2024-01-01","2024-02-01")
 def test_roundtrip_and_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d);payload=json.dumps(sample()).encode()
   result=u.fetch("2024-01-01","2024-02-01",folder=folder,opener=lambda req,timeout:Response(payload))
   self.assertEqual(len(u.load(folder)["records"]),1)
   with self.assertRaises(FileExistsError):u.fetch("2024-01-01","2024-02-01",folder=folder,opener=lambda req,timeout:Response(payload))
   snap=next(folder.glob("usgs-*.json"));snap.write_text("[]")
   with self.assertRaises(ValueError):u.load(folder)
 def test_count_mismatch_is_diagnostic(self):
  x=sample();x["metadata"]["count"]=10
  with self.assertRaisesRegex(ValueError,"metadata_count=10, returned_features=1"):u.normalize(x,"2024-01-01","2024-02-01")
 def test_optional_metadata_count_matches_real_usgs_response(self):
  x=sample();del x["metadata"]["count"]
  rows=u.normalize(x,"2024-01-01","2024-02-01")
  self.assertEqual(len(rows),1)
 def test_invalid_present_count_rejected(self):
  x=sample();x["metadata"]["count"]="1"
  with self.assertRaisesRegex(ValueError,"count mismatch"):u.normalize(x,"2024-01-01","2024-02-01")
 def test_powerbi_contract(self):
  x=(ROOT/"dashboards/powerbi/Update_DataNexus_Overview.py").read_text()
  self.assertIn("seismic_events",x)
  y=(ROOT/"dashboards/powerbi/DataNexus_EndToEnd.SemanticModel/definition/model.tmdl").read_text()
  self.assertIn("ref table SeismicEvents",y)
