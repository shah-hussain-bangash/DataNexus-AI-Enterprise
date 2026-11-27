"""No-network NOAA daily-summaries connector and Power BI contract tests."""
import io,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import ingest_noaa_weather as noaa
def fixture():
 return [{"STATION":noaa.STATION,"DATE":"2024-01-01","TMAX":"5.2","TMIN":"-2.1","PRCP":"0.5"}]
class Response:
 def __init__(self,data):self.stream=io.BytesIO(data)
 def __enter__(self):return self
 def __exit__(self,*args):self.stream.close()
 def read(self,n):return self.stream.read(n)
class NOAAWeatherTests(unittest.TestCase):
 def test_bounded_official_url(self):
  self.assertTrue(noaa.url_for("2024-01-01","2024-01-31").startswith("https://www.ncei.noaa.gov/access/services/data/v1?"))
  with self.assertRaises(ValueError):noaa.url_for("2024-01-01","2024-04-01")
  with self.assertRaises(ValueError):noaa.url_for("2024-01-01","2024-01-31","OTHER")
 def test_missing_optional_measurement_preserved(self):
  row=fixture()[0];row.pop("PRCP")
  self.assertIsNone(noaa.normalize([row],"2024-01-01","2024-01-31")[0]["precip_mm"])
 def test_reject_duplicate_and_other_station(self):
  with self.assertRaises(ValueError):noaa.normalize(fixture()*2,"2024-01-01","2024-01-31")
  row=fixture()[0];row["STATION"]="UNKNOWN"
  with self.assertRaises(ValueError):noaa.normalize([row],"2024-01-01","2024-01-31")
 def test_invalid_temperature_and_precipitation(self):
  row=fixture()[0];row["TMIN"]="35"
  with self.assertRaises(ValueError):noaa.normalize([row],"2024-01-01","2024-01-31")
  row=fixture()[0];row["PRCP"]="-1"
  with self.assertRaises(ValueError):noaa.normalize([row],"2024-01-01","2024-01-31")
 def test_verified_snapshot_and_tampering(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d);data=json.dumps(fixture()).encode()
   result=noaa.fetch("2024-01-01","2024-01-31",folder=path,opener=lambda req,timeout:Response(data))
   self.assertEqual(result["records"],1)
   self.assertEqual(noaa.load(path)["records"][0]["tmax_c"],5.2)
   with self.assertRaises(FileExistsError):noaa.fetch("2024-01-01","2024-01-31",folder=path)
   snapshot=path/(next(path.glob("noaa-daily-*.json")).name)
   snapshot.write_text("[]")
   with self.assertRaises(ValueError):noaa.load(path)
 def test_powerbi_weather_contract(self):
  overview=(ROOT/"dashboards/powerbi/Update_DataNexus_Overview.py").read_text()
  model=(ROOT/"dashboards/powerbi/DataNexus_EndToEnd.SemanticModel/definition/model.tmdl").read_text()
  self.assertIn("'weather_daily':weather",overview)
  self.assertIn("ref table WeatherDaily",model)
