"""Phase 3.12 isolation, state validation and synthetic event contract."""
import importlib.util,hashlib,json,sys,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("lab",ROOT/"scripts/mta_restart_lab.py")
lab=importlib.util.module_from_spec(sp);sp.loader.exec_module(lab)
class RestartLabContractTests(unittest.TestCase):
 def test_payload_is_synthetic_and_bounded(self):
  doc=lab.validate_record(lab.make_payload("before"))
  self.assertTrue(doc["synthetic"]);self.assertFalse(doc["production_approved"])
  self.assertLess(len(lab.make_payload("before")),1024)
 def test_reject_invalid_lab_payload(self):
  bad=json.loads(lab.make_payload("before"))
  bad["kind"]="live"
  with self.assertRaises(ValueError):lab.validate_record(json.dumps(bad).encode())
 def test_reject_invalid_prepared_state(self):
  with self.assertRaises(ValueError):lab.validate_state({"state":"prepared"})
 def test_exact_isolated_broker_topic_and_group(self):
  self.assertEqual(lab.BOOTSTRAP,"127.0.0.1:29092")
  self.assertEqual(lab.TOPIC,"datanexus.mta.restart.lab.v1")
  self.assertNotEqual(lab.GROUP,"datanexus-mta-aggregate-v1")
 def test_lab_compose_is_separate_from_main_project(self):
  text=(ROOT/"docker-compose.mta-restart-lab.yml").read_text()
  self.assertIn("name: datanexus-mta-restart-lab",text)
  self.assertIn("127.0.0.1:29092:29092",text)
  self.assertIn("datanexus_mta_restart_lab_data",text)
  self.assertNotIn("19092:19092",text)
  self.assertNotIn("./data/dev",text)
 def test_no_dangerous_main_broker_commands(self):
  source=(ROOT/"scripts/mta_restart_lab.py").read_text()
  self.assertNotIn("aviation.states.v1",source)
  self.assertNotIn("docker compose down",source)
  self.assertNotIn("delete_topics",source)
  self.assertNotIn("19092",source)
 def test_existing_state_is_not_overwritten(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/"state.json"
   f.write_text("{}")
   with self.assertRaises(FileExistsError):lab.prepare(f)
 def test_versioned_validation_rejects_extra_fields(self):
  data=json.loads(lab.make_payload("before"));data["extra"]="untrusted"
  with self.assertRaises(ValueError):lab.validate_record(json.dumps(data).encode())
