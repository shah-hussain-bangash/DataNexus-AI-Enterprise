"""Phase 3.11 backup evidence tests, no broker and no production data."""
import importlib.util,json,sys,tempfile,unittest
from contextlib import closing
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]
for folder in ("scripts","apps/api"):sys.path.insert(0,str(ROOT/folder))
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);mod=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(mod);return mod
backup=load("scripts/backup_verify_mta.py","mta_backup_evidence")
r=load("scripts/report_mta_recovery.py","mta_recovery_report")
api=load("apps/api/mta_recovery_evidence.py","mta_recovery_api")
class RecoveryEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name);self.data=self.root/"mta"
  self.data.mkdir()
  self.backup=self.data/"recovery_backups"/"mta-recovery-20261127T070000000000Z.sqlite3"
  self.backup.parent.mkdir()
  import sqlite3
  with closing(sqlite3.connect(self.backup)) as db:
   db.execute("CREATE TABLE mta_aggregates (event_id TEXT,provider_timestamp_utc TEXT,observed_at_utc TEXT,feed_id TEXT,response_sha256 TEXT,entities INT,trip_updates INT,vehicle_positions INT,alerts INT)")
   db.execute("INSERT INTO mta_aggregates VALUES (?,?,?,?,?,?,?,?,?)",("a"*64,"2026-11-27T07:00:00+00:00","2026-11-27T07:00:01+00:00","ace","b"*64,8,4,4,0))
   db.commit()
 def saved(self):
  result=r.verify_existing_backup(self.backup)
  r.save_report(result,self.data/"recovery_reports")
  return result
 def test_backup_restore_integrity_and_api_report(self):
  rec=self.saved();self.assertEqual(rec["backup_records"],1)
  response=api.latest_recovery(self.root,now=datetime.now(timezone.utc)+timedelta(seconds=1))
  self.assertTrue(response["report"]["backup_integrity_digest_matches"])
  self.assertFalse(response["report"]["kafka_recovery_tested"])
 def test_no_report_is_not_health(self):
  self.assertIsNone(api.latest_recovery(self.root)["report"])
 def test_tampered_backup_fails_closed(self):
  self.saved()
  with self.backup.open("ab") as f:f.write(b"corruption")
  with self.assertRaisesRegex(ValueError,"changed"):api.latest_recovery(self.root)
 def test_corrupt_report_does_not_approve(self):
  self.saved()
  file=next((self.data/"recovery_reports").glob("*.json"))
  obj=json.loads(file.read_text());obj["production_approved"]=True;file.write_text(json.dumps(obj))
  with self.assertRaises(ValueError):api.latest_recovery(self.root)
 def test_future_report_fails_closed(self):
  self.saved()
  with self.assertRaises(ValueError):
   api.latest_recovery(self.root,now=datetime(2020,1,1,tzinfo=timezone.utc))
 def test_api_contract_and_aviation_isolation(self):
  main=(ROOT/"apps/api/main.py").read_text()
  proxy=(ROOT/"apps/web/app/api/portal/[...path]/route.ts").read_text()
  self.assertIn('"/api/v1/mta/recovery"',main)
  self.assertIn('"mta/recovery"',proxy)
  self.assertIn('require_permission("quality:read")',main)
  self.assertNotIn("aviation.states.v1",(ROOT/"scripts/report_mta_recovery.py").read_text())
