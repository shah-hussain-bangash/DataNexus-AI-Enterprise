"""Dependency-free tests of process-local login throttling."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("login_throttle", ROOT / "apps/api/login_throttle.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LoginThrottleTests(unittest.TestCase):
    def setUp(self):
        self.limiter = module.LoginThrottle()

    def test_five_failures_trigger_lockout(self):
        for timepoint in range(5):
            self.assertEqual(self.limiter.retry_after("admin", now=float(timepoint)), 0)
            self.assertTrue(self.limiter.failure("admin", now=float(timepoint)))
        self.assertGreater(self.limiter.retry_after("admin", now=5.0), 0)

    def test_window_expiry_clears_lockout(self):
        for point in range(5):
            self.limiter.failure("admin", now=float(point))
        self.assertEqual(self.limiter.retry_after("admin", now=301.0), 0)

    def test_success_resets_only_that_identity(self):
        for point in range(5):
            self.limiter.failure("admin", now=float(point))
            self.limiter.failure("other", now=float(point))
        self.limiter.success("ADMIN")
        self.assertEqual(self.limiter.retry_after("admin", now=5.0), 0)
        self.assertGreater(self.limiter.retry_after("other", now=5.0), 0)

    def test_identity_storage_is_bounded(self):
        self.limiter._failures = {str(i): [100.0] for i in range(module.MAX_IDENTITIES)}
        self.assertTrue(self.limiter.saturated("new", now=101.0))
        self.assertFalse(self.limiter.failure("new", now=101.0))
        self.assertFalse(self.limiter.saturated("new", now=401.0))


if __name__ == "__main__":
    unittest.main()
