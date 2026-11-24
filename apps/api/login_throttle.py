"""Bounded, process-local login failure throttling for the local prototype.

Not distributed, not persistent, and not a substitute for an identity
provider with centrally enforced account/network protections.
"""
import threading
import time

MAX_FAILURES = 5
WINDOW_SECONDS = 300
MAX_IDENTITIES = 2048


class LoginThrottle:
    def __init__(self):
        self._lock = threading.Lock()
        self._failures = {}

    @staticmethod
    def _key(username):
        return username.strip().casefold()[:100]

    def _prune(self, now):
        expired = [key for key, values in self._failures.items()
                   if not values or values[-1] <= now - WINDOW_SECONDS]
        for key in expired:
            del self._failures[key]

    def retry_after(self, username, now=None):
        now = time.monotonic() if now is None else now
        with self._lock:
            self._prune(now)
            values = self._failures.get(self._key(username), ())
            if len(values) < MAX_FAILURES:
                return 0
            return max(1, int(values[0] + WINDOW_SECONDS - now + 0.999))

    def failure(self, username, now=None):
        now = time.monotonic() if now is None else now
        with self._lock:
            self._prune(now)
            key = self._key(username)
            if key not in self._failures and len(self._failures) >= MAX_IDENTITIES:
                # Fail closed when storage is saturated: do not admit
                # new identifiers indefinitely or grow memory unbounded.
                return False
            values = self._failures.setdefault(key, [])
            values[:] = [t for t in values if t > now - WINDOW_SECONDS]
            if len(values) < MAX_FAILURES:
                values.append(now)
            return True

    def saturated(self, username, now=None):
        now = time.monotonic() if now is None else now
        with self._lock:
            self._prune(now)
            return self._key(username) not in self._failures and len(self._failures) >= MAX_IDENTITIES

    def success(self, username):
        with self._lock:
            self._failures.pop(self._key(username), None)


throttle = LoginThrottle()
