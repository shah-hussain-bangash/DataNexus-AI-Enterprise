"""Read-only, evidence-backed answers for the local NYC taxi reporting snapshot."""

from calendar import monthrange
from datetime import date


QUESTIONS = {
    "trip_total": (
        "How many accepted taxi trips were there in January 2024?",
        "How many taxi trips were there?",
        "What was the total trip count?",
    ),
    "peak_day": (
        "Which day had the most taxi trips in January 2024?",
        "Which day had the most trips?",
        "What was the busiest day?",
    ),
    "daily_average": (
        "What was the average daily taxi trip count in January 2024?",
        "What was the average daily trip count?",
    ),
    "coverage": (
        "What dates does the taxi report cover?",
        "What is the taxi reporting period?",
    ),
}


def normalize(question):
    return " ".join(question.casefold().split()).removesuffix("?").rstrip()


QUESTION_KEYS = {
    normalize(question): key for key, questions in QUESTIONS.items() for question in questions
}


def answer_question(question, load_snapshot):
    key = QUESTION_KEYS.get(normalize(question))
    if key is None:
        return {
            "status": "unsupported",
            "answer": "This assistant can answer a limited set of questions about the local January 2024 NYC taxi snapshot.",
            "supported_questions": [questions[0] for questions in QUESTIONS.values()],
            "citations": [],
        }

    snapshot = load_snapshot()
    month = snapshot["source_month"]
    first = date.fromisoformat(month + "-01")
    day_count = monthrange(first.year, first.month)[1]
    daily = {}
    for row in snapshot["daily"]:
        day = date.fromisoformat(row["date"])
        in_month = (day.year, day.month) == (first.year, first.month)
        if row.get("within_source_month") is not in_month:
            raise ValueError("Snapshot date flags are inconsistent")
        if in_month:
            if day in daily:
                raise ValueError("Duplicate in-month reporting date")
            daily[day] = row["trip_count"]
    total = sum(daily.values())
    if len(daily) != day_count or snapshot.get("in_month_days") != day_count or snapshot["in_month_trip_count"] != total:
        raise ValueError("In-month reporting evidence does not reconcile")

    last = first.replace(day=day_count)
    period = first.strftime("%B %Y")
    if key == "trip_total":
        answer = f"The local NYC Yellow Taxi report contains {total:,} accepted pickup trips in {period}."
        value = {"trips": total}
        fields = ["in_month_trip_count"]
    elif key == "peak_day":
        peak = max(daily.values())
        dates = sorted(day.isoformat() for day, count in daily.items() if count == peak)
        answer = f"The highest daily count in {period} was {peak:,} trips on {', '.join(dates)}."
        value = {"trips": peak, "dates": dates}
        fields = ["daily.date", "daily.trip_count", "daily.within_source_month"]
    elif key == "daily_average":
        average = round(total / day_count, 2)
        answer = f"The local report averaged {average:,.2f} accepted trips per day in {period}."
        value = {"trips_per_day": average, "days": day_count}
        fields = ["in_month_trip_count", "in_month_days"]
    else:
        answer = f"The local report covers {first.isoformat()} through {last.isoformat()} for accepted pickups."
        value = {"start": first.isoformat(), "end": last.isoformat(), "days": day_count}
        fields = ["source_month", "in_month_days"]

    return {
        "status": "answered",
        "answer": answer,
        "value": value,
        "citations": [{
            "source_id": "nyc_tlc_yellow_taxi.local_gold",
            "reporting_endpoint": "/api/v1/nyc-tlc/reporting",
            "start": first.isoformat(),
            "end": last.isoformat(),
            "gold_sha256": snapshot["gold_sha256"],
            "fields": fields,
        }],
    }
