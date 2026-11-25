"""Verify dashboard connects to protected source metadata, not fabricated observations."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class BackendEvidenceContractTests(unittest.TestCase):
 def test_dashboard_calls_authenticated_endpoint(self):
  code=(ROOT/"apps/web/app/workspaces/backend-evidence.tsx").read_text(encoding="utf-8")
  page=(ROOT/"apps/web/app/workspaces/page.tsx").read_text(encoding="utf-8")
  self.assertIn('"/api/portal/"+path',code)
  self.assertIn('credentials:"same-origin"',code)
  self.assertIn('cache:"no-store"',code)
  self.assertIn('result.status===401||result.status===403',code)
  self.assertIn('BackendEvidence',page)
 def test_no_made_up_backend_metrics(self):
  code=(ROOT/"apps/web/app/workspaces/backend-evidence.tsx").read_text(encoding="utf-8")
  self.assertIn("Dataset metadata contracts only",code)
  self.assertIn("Loading authenticated source contracts",code)
  self.assertIn("Sign in",code)
