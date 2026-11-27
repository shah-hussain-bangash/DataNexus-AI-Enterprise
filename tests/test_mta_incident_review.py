"""Phase 3.9 review transitions; local synthetic evidence, no broker, no network."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("review",ROOT/"apps/api/mta_incident_review.py")
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
DIGEST="a"*64
class ReviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  folder=self.root/"mta"/"alert_history";folder.mkdir(parents=True)
  t=(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat()
  self.file=folder/("mta-alert-"+DIGEST+".json")
  self.file.write_text(json.dumps({"snapshot_sha256":DIGEST,"incident_lifecycle":"unreviewed",
   "alert_count":1,"status":"attention","alerts":[{"code":"STORED_OBSERVATION_OLD"}],
   "assessed_at_utc":t}))
 def test_valid_lifecycle_and_review_history(self):
  self.assertEqual(r.review_status(self.root)["incidents"][0]["review_state"],"unreviewed")
  r.append_review(self.root,DIGEST,"acknowledge","operator_1","Reviewed the stale snapshot")
  r.append_review(self.root,DIGEST,"assign","operator_1","Assigned manual follow up","operator_2")
  result=r.append_review(self.root,DIGEST,"resolve","operator_2","Reviewed new source evidence",evidence_reference="mta-monitor-20261127T100000000000Z.json")
  self.assertEqual(result["sequence"],3)
  self.assertEqual(r.review_status(self.root)["incidents"][0]["review_state"],"resolved")
  self.assertTrue(r.review_status(self.root)["incidents"][0]["resolution_self_reported"])
  self.assertEqual(len(r.records(self.root,DIGEST)),3)
 def test_mandatory_order_and_resolution_evidence(self):
  with self.assertRaises(ValueError):r.append_review(self.root,DIGEST,"resolve","operator_1","Cannot skip other states",evidence_reference="valid-evidence-file")
  r.append_review(self.root,DIGEST,"acknowledge","operator_1","Reviewed and accepted queue")
  with self.assertRaises(ValueError):r.append_review(self.root,DIGEST,"assign","operator_1","Assign next engineer")
  r.append_review(self.root,DIGEST,"assign","operator_1","Assign next engineer","operator_2")
  with self.assertRaises(ValueError):r.append_review(self.root,DIGEST,"resolve","operator_2","No evidence offered")
 def test_immutable_original_and_duplicate_transition(self):
  before=self.file.read_bytes()
  r.append_review(self.root,DIGEST,"acknowledge","operator_1","Reviewed monitoring details")
  self.assertEqual(before,self.file.read_bytes())
  with self.assertRaises(ValueError):r.append_review(self.root,DIGEST,"acknowledge","operator_1","Repeated acknowledgment")
 def test_tampered_chain_rejected(self):
  r.append_review(self.root,DIGEST,"acknowledge","operator_1","Reviewed monitoring details")
  file=r.directory_for(self.root)/DIGEST/"0001.json"
  doc=json.loads(file.read_text());doc["note"]="Edited old evidence";file.write_text(json.dumps(doc))
  # First action has no previous digest; check against a subsequent chained action.
  r.append_review(self.root,DIGEST,"assign","operator_1","Assign and investigate","operator_2")
  doc=json.loads(file.read_text());doc["note"]="Edited again after assignment";file.write_text(json.dumps(doc))
  with self.assertRaisesRegex(ValueError,"chain"):r.records(self.root,DIGEST)
 def test_invalid_actor_and_reference_rejected(self):
  with self.assertRaises(ValueError):r.append_review(self.root,DIGEST,"acknowledge","bad actor!","Reviewed the incident")
  with self.assertRaises(ValueError):r.append_review(self.root,"invalid","acknowledge","operator_1","Reviewed the incident")
 def test_api_contract_and_no_kafka_mutations(self):
  main=(ROOT/"apps/api/main.py").read_text()
  proxy=(ROOT/"apps/web/app/api/portal/[...path]/route.ts").read_text()
  self.assertIn('"/api/v1/mta/incident-reviews"',main)
  self.assertIn('"mta/incident-reviews"',proxy)
  self.assertIn('require_permission("quality:read")',main)
  text=(ROOT/"apps/api/mta_incident_review.py").read_text()
  self.assertNotIn("aviation.states.v1",text)
  self.assertNotIn("consumer.commit",text)
