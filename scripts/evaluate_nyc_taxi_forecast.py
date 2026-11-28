"""Evaluate fixed-origin NYC taxi trip-count baselines on an existing local reporting snapshot."""

import argparse
from calendar import monthrange
from datetime import date
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


HORIZON = 7
MAX_SNAPSHOT_BYTES = 128 * 1024


def load_daily(snapshot_path):
    with snapshot_path.open("rb") as stream:
        raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise ValueError("Reporting snapshot exceeds the bounded input size")
    snapshot = json.loads(raw)
    if not isinstance(snapshot, dict) or (
        snapshot.get("source") != "nyc_tlc_yellow_taxi"
        or snapshot.get("stage") != "local_historical_reporting_preview"
    ):
        raise ValueError("Expected an existing local NYC TLC Yellow Taxi reporting snapshot")
    month = snapshot.get("source_month")
    if not isinstance(month, str) or len(month) != 7:
        raise ValueError("Invalid source month")
    first_day = date.fromisoformat(month + "-01")
    month_days = monthrange(first_day.year, first_day.month)[1]
    expected = {first_day.replace(day=i) for i in range(1, month_days + 1)}

    rows = snapshot.get("daily")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 400:
        raise ValueError("Invalid daily reporting rows")
    by_date = {}
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("date"), str):
            raise ValueError("Invalid daily reporting date")
        day = date.fromisoformat(row["date"])
        if day in seen:
            raise ValueError("Duplicate daily reporting date")
        seen.add(day)
        count = row.get("trip_count")
        if type(count) is not int or count < 0:
            raise ValueError("Expected nonnegative whole trip counts")
        in_scope = day in expected
        if row.get("within_source_month") is not in_scope:
            raise ValueError("Date disagrees with the source-month flag")
        if in_scope:
            by_date[day] = count
    if set(by_date) != expected:
        raise ValueError("Forecasting requires a complete source month with one observation per day")
    if snapshot.get("in_month_days") != month_days or snapshot.get("in_month_trip_count") != sum(by_date.values()):
        raise ValueError("Daily observations do not reconcile with the source-month reporting totals")
    return sorted(by_date.items()), hashlib.sha256(raw).hexdigest(), month


def metrics(actuals, forecasts):
    errors = [prediction - actual for actual, prediction in zip(actuals, forecasts, strict=True)]
    absolute_error = sum(abs(error) for error in errors)
    actual_total = sum(actuals)
    return {
        "mae_trips": round(absolute_error / len(errors), 2),
        "wape_percent": round(100 * absolute_error / actual_total, 2) if actual_total else None,
        "bias_trips": round(sum(errors) / len(errors), 2),
    }


def evaluate(snapshot_path):
    daily, fingerprint, month = load_daily(snapshot_path)
    train = daily[:-HORIZON]
    holdout = daily[-HORIZON:]
    same_weekday = [count for _, count in train[-HORIZON:]]
    last_day = [train[-1][1]] * HORIZON
    actuals = [count for _, count in holdout]
    return {
        "status": "local_historical_baseline",
        "source": "nyc_tlc_yellow_taxi",
        "source_month": month,
        "reporting_snapshot_sha256": fingerprint,
        "target": "accepted daily pickup trips within the source month",
        "training": {"start": train[0][0].isoformat(), "end": train[-1][0].isoformat(), "days": len(train)},
        "holdout": {"start": holdout[0][0].isoformat(), "end": holdout[-1][0].isoformat(), "days": len(holdout)},
        "models": {
            "seasonal_naive_7_day": metrics(actuals, same_weekday),
            "last_observation": metrics(actuals, last_day),
        },
        "holdout_rows": [
            {"date": day.isoformat(), "actual": count, "seasonal_naive_7_day": seasonal, "last_observation": naive}
            for (day, count), seasonal, naive in zip(holdout, same_weekday, last_day, strict=True)
        ],
        "live_forecast": False,
        "production_approved": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.snapshot.resolve() == args.output.resolve():
        parser.error("The output must be separate from the source snapshot")
    result = evaluate(args.snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".json", dir=args.output.parent, delete=False,
        ) as stream:
            temp = Path(stream.name)
            json.dump(result, stream, indent=2)
            stream.write("\n")
        os.replace(temp, args.output)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    print(json.dumps({"training": result["training"], "holdout": result["holdout"], "models": result["models"]}, indent=2))


if __name__ == "__main__":
    main()
