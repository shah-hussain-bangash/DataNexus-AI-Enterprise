import json
import tempfile
import unittest
from pathlib import Path
from datanexus.events import normalize_states, validate_envelope
from datanexus.storage import LocalEventStore
from datanexus.opensky import OpenSkyClient

FIXTURE = Path(__file__).parent / "fixtures" / "opensky-states.json"


class StreamingTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text())
        self.events = normalize_states(self.fixture, collected_at="2026-01-01T00:00:00Z")

    def test_normalize_and_schema(self):
        self.assertEqual(len(self.events), 2)
        self.assertEqual(self.events[0]["payload"]["icao24"], "896a1b")
        self.assertEqual(validate_envelope(self.events[0]), self.events[0])

    def test_deterministic_event_ids(self):
        other = normalize_states(self.fixture, collected_at="2026-02-01T00:00:00Z")
        self.assertEqual([e["event_id"] for e in self.events], [e["event_id"] for e in other])

    def test_deduplicate_after_restart(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "aviation.db"
            store = LocalEventStore(path)
            self.assertTrue(store.put(self.events[0]))
            self.assertFalse(store.put(self.events[0]))
            store.close()
            store = LocalEventStore(path)
            self.assertFalse(store.put(self.events[0]))
            self.assertEqual(store.count(), 1)
            store.close()

    def test_invalid_event_rejected(self):
        broken = dict(self.events[0])
        broken["tenant_id"] = ""
        with self.assertRaises(ValueError):
            validate_envelope(broken)

    def test_invalid_bbox_rejected_without_network(self):
        client = OpenSkyClient(client_id="", client_secret="")
        with self.assertRaises(ValueError):
            client.states((30, 50, 20, 60))

    def test_malformed_rows_are_ignored(self):
        data = {"time": 1767225600, "states": [["bad"], None]}
        self.assertEqual(normalize_states(data), [])


if __name__ == "__main__":
    unittest.main()
