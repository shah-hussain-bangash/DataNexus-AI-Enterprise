from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from uuid import uuid4

from datanexus.banking import ingest_credit_feed


class BankingFeedTests(TestCase):
    def test_source_scoped_cursor_does_not_count_replayed_booking_twice(self):
        source, case = str(uuid4()), str(uuid4())
        booking = {"schema_version": 1, "sequence": 1, "event_id": "banking-demo:1", "case_id": case,
                   "event_type": "booking_reconciled", "occurred_at": "2026-11-01T00:00:00Z",
                   "booked_amount_aed": 175000}

        def feed(after):
            return {"source_id": source, "events": [] if after else [booking], "next_after": 1, "has_more": False}

        with TemporaryDirectory() as folder:
            path = Path(folder) / "reporting.sqlite3"
            first = ingest_credit_feed(path, feed)
            second = ingest_credit_feed(path, feed)
            self.assertEqual((first["new_events"], second["new_events"]), (1, 0))
            self.assertEqual(second["booked_facilities"], 1)
            self.assertEqual(second["booked_exposure_aed"], 175000)
