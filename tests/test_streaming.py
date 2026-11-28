import json
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from pathlib import Path
from datanexus import cli
from datanexus.events import normalize_states, validate_envelope
from datanexus.storage import LocalEventStore
from datanexus.opensky import OpenSkyClient, OpenSkyRateLimited

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


class LiveOnceTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_795_850_000
        self.response = json.loads(FIXTURE.read_text())
        self.response["time"] = self.now
        for state in self.response["states"]:
            state[4] = self.now
        self.client = Mock(client_id="test-client", client_secret="test-secret")
        self.client.states.return_value = self.response
        self.args = SimpleNamespace(bootstrap="127.0.0.1:39092", topic="aviation.states.authorized.v1")
        self.bbox = (24.8, 54.9, 25.3, 55.6)

    @patch.object(cli, "produce")
    def test_fetches_once_and_publishes_normalized_events(self, publish):
        with patch.object(cli.time, "time", return_value=self.now):
            cli.collect_live_once(self.args, self.client, self.bbox)
        self.client.states.assert_called_once_with(self.bbox)
        publish.assert_called_once()
        records, bootstrap, topic = publish.call_args.args
        self.assertEqual(len(records), 2)
        self.assertTrue(all(event["source"] == "opensky.states.all" for event in records))
        self.assertEqual((bootstrap, topic), (self.args.bootstrap, self.args.topic))

    @patch.object(cli, "produce")
    def test_missing_credentials_prevent_provider_and_kafka_calls(self, publish):
        self.client.client_secret = ""
        with self.assertRaisesRegex(SystemExit, "OPENSKY_CLIENT_SECRET"):
            cli.collect_live_once(self.args, self.client, self.bbox)
        self.client.states.assert_not_called()
        publish.assert_not_called()

    @patch.object(cli, "produce")
    def test_stale_future_invalid_and_empty_snapshots_do_not_publish(self, publish):
        scenarios = [
            ({"time": self.now - 121}, "outside the live acceptance window"),
            ({"time": self.now + 31}, "outside the live acceptance window"),
            ({"time": True}, "invalid snapshot timestamp"),
            ({"time": self.now, "states": []}, "no valid aircraft events"),
        ]
        for response, error in scenarios:
            with self.subTest(response=response), patch.object(cli.time, "time", return_value=self.now):
                self.client.states.return_value = response
                with self.assertRaisesRegex(SystemExit, error):
                    cli.collect_live_once(self.args, self.client, self.bbox)
        self.assertEqual(self.client.states.call_count, len(scenarios))
        publish.assert_not_called()

    @patch.object(cli, "produce")
    def test_rate_limit_neither_retries_nor_publishes(self, publish):
        self.client.states.side_effect = OpenSkyRateLimited(120)
        with self.assertRaisesRegex(SystemExit, "Retry after 120 seconds"):
            cli.collect_live_once(self.args, self.client, self.bbox)
        self.client.states.assert_called_once()
        publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
