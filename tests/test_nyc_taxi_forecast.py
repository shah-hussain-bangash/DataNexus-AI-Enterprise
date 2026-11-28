"""Verify no holdout leakage and fail-closed handling of corrupted source-month inputs."""
import json
from datetime import date
from pathlib import Path
import tempfile
import unittest

from scripts.evaluate_nyc_taxi_forecast import evaluate, load_daily


def month_snapshot():
    daily = [
        {"date": date(2024, 1, day).isoformat(), "trip_count": day, "within_source_month": True}
        for day in range(1, 32)
    ]
    daily.append({"date": "2024-02-01", "trip_count": 10000, "within_source_month": False})
    return {
        "stage": "local_historical_reporting_preview",
        "source": "nyc_tlc_yellow_taxi",
        "source_month": "2024-01",
        "daily": list(reversed(daily)),
        "in_month_days": 31,
        "in_month_trip_count": sum(range(1, 32)),
    }


class TaxiForecastTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "preview.json"

    def put(self, snapshot):
        self.path.write_text(json.dumps(snapshot), encoding="utf-8")

    def test_forecasts_use_fixed_training_origin(self):
        original = month_snapshot()
        self.put(original)
        baseline = evaluate(self.path)
        self.assertEqual(baseline["training"], {"start": "2024-01-01", "end": "2024-01-24", "days": 24})
        self.assertEqual(baseline["holdout"], {"start": "2024-01-25", "end": "2024-01-31", "days": 7})
        self.assertEqual([row["seasonal_naive_7_day"] for row in baseline["holdout_rows"]], list(range(18, 25)))
        self.assertEqual([row["last_observation"] for row in baseline["holdout_rows"]], [24] * 7)
        self.assertEqual(baseline["models"]["seasonal_naive_7_day"]["mae_trips"], 7.0)
        self.assertEqual(baseline["models"]["last_observation"]["mae_trips"], 4.0)

        for row in original["daily"]:
            if "2024-01-25" <= row["date"] <= "2024-01-31":
                row["trip_count"] += 1000
        original["in_month_trip_count"] += 7000
        self.put(original)
        altered = evaluate(self.path)
        for key in ("seasonal_naive_7_day", "last_observation"):
            self.assertEqual([row[key] for row in baseline["holdout_rows"]],
                             [row[key] for row in altered["holdout_rows"]])
            self.assertGreater(altered["models"][key]["mae_trips"], baseline["models"][key]["mae_trips"])

    def test_missing_duplicate_misflagged_and_unreconciled_days_are_rejected(self):
        original = month_snapshot()
        rows = original["daily"]
        cases = [
            ({**original, "daily": rows[:-1]}, "complete source month"),
            ({**original, "daily": rows + rows[-1:]}, "Duplicate"),
            ({**original, "daily": [{**rows[0], "within_source_month": True}, *rows[1:]]}, "source-month flag"),
            ({**original, "in_month_trip_count": 0}, "do not reconcile"),
        ]
        for snapshot, reason in cases:
            with self.subTest(reason=reason):
                self.put(snapshot)
                with self.assertRaisesRegex(ValueError, reason):
                    load_daily(self.path)

    def test_zero_actual_total_reports_wape_as_undefined(self):
        original = month_snapshot()
        for row in original["daily"]:
            if "2024-01-25" <= row["date"] <= "2024-01-31":
                row["trip_count"] = 0
        original["in_month_trip_count"] = sum(range(1, 25))
        self.put(original)
        result = evaluate(self.path)
        self.assertIsNone(result["models"]["seasonal_naive_7_day"]["wape_percent"])


if __name__ == "__main__":
    unittest.main()
