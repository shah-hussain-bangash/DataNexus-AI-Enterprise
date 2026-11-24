"""Read-only SQLite event queries for the initial DataNexus portal.

Do not infer Kafka, Spark, Iceberg, or S3 health from this SQLite database.
When unavailable, APIs expose explicit unconfigured status rather than mock data.
"""
import json
import sqlite3
from contextlib import closing
from pathlib import Path


def read_events(path, limit=100, query=""):
    db_path = Path(path)
    if not db_path.is_file():
        return {"configured": False, "events": [], "total": 0, "message": "SQLite event sink not found. Run the Phase 2A consumer to populate data/dev/aviation.sqlite3."}
    limit = max(1, min(int(limit), 500))
    with closing(sqlite3.connect(f"file:{db_path.resolve().as_posix()}?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        search = "%" + query.strip()[:80].replace("%", r"\%").replace("_", r"\_") + "%"
        where = "WHERE (icao24 LIKE ? ESCAPE '\\' OR tenant_id LIKE ? ESCAPE '\\')" if query.strip() else ""
        params = (search, search) if where else ()
        total = connection.execute("SELECT COUNT(*) FROM events " + where, params).fetchone()[0]
        rows = connection.execute(
            "SELECT event_id, source_time, tenant_id, icao24, latitude, longitude, raw_json FROM events "
            + where + " ORDER BY source_time DESC, event_id DESC LIMIT ?", (*params, limit),
        ).fetchall()
        events = []
        for row in rows:
            data = dict(row)
            raw = json.loads(data.pop("raw_json"))
            payload = raw.get("payload", {})
            events.append({
                **data,
                "callsign": payload.get("callsign"),
                "velocity_mps": payload.get("velocity_mps"),
                "altitude_m": payload.get("geo_altitude_m"),
                "on_ground": payload.get("on_ground"),
                "source": raw.get("source", "unknown"),
            })
    return {"configured": True, "events": events, "total": total, "message": None}


def summarize_events(result):
    rows = result["events"]
    ids = {row["event_id"] for row in rows}
    positions = sum(row["latitude"] is not None and row["longitude"] is not None for row in rows)
    unique_aircraft = len({row["icao24"] for row in rows})
    tenants = len({row["tenant_id"] for row in rows})
    return {
        "source": "local_sqlite",
        "configured": result["configured"],
        "limited_to": "first 500 most recent matched records",
        "sample_size": len(rows),
        "total_events": result["total"],
        "aircraft_in_sample": unique_aircraft,
        "positions_in_sample": positions,
        "tenants_in_sample": tenants,
        "duplicate_ids_in_sample": len(rows) - len(ids),
        "last_source_event_at": rows[0]["source_time"] if rows else None,
        "message": result["message"],
    }
