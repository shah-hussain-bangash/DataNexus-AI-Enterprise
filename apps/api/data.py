"""Read-only tenant-scoped SQLite queries for local portal."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

def read_events(path, limit=100, query="", tenant_id=None):
    db_path = Path(path)
    if not db_path.is_file():
        return {"configured": False, "events": [], "total": 0,
                "message": "SQLite event sink not found. Run Phase 2A consumer."}
    limit = max(1, min(int(limit), 500))
    with closing(sqlite3.connect("file:" + db_path.resolve().as_posix() + "?mode=ro", uri=True)) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.row_factory = sqlite3.Row
        predicates = []
        params = []
        if tenant_id is not None:
            predicates.append("tenant_id = ?")
            params.append(tenant_id)
        if query.strip():
            search = "%" + query.strip()[:80].replace("%", "").replace("_", "") + "%"
            predicates.append("(LOWER(icao24) LIKE LOWER(?) OR LOWER(tenant_id) LIKE LOWER(?))")
            params.extend([search, search])
        where = "WHERE " + " AND ".join(predicates) if predicates else ""
        total = connection.execute("SELECT COUNT(*) FROM events " + where, params).fetchone()[0]
        rows = connection.execute(
            "SELECT event_id, source_time, tenant_id, icao24, latitude, longitude, raw_json FROM events "
            + where + " ORDER BY source_time DESC, event_id DESC LIMIT ?", [*params, limit],
        ).fetchall()
        events = []
        for row in rows:
            record = dict(row)
            raw = json.loads(record.pop("raw_json"))
            payload = raw.get("payload", {})
            events.append({
                **record,
                "callsign": payload.get("callsign"),
                "velocity_mps": payload.get("velocity_mps"),
                "altitude_m": payload.get("geo_altitude_m"),
                "on_ground": payload.get("on_ground"),
                "source": raw.get("source", "unknown"),
            })
    return {"configured": True, "events": events, "total": total, "message": None}

def summarize_events(result):
    rows = result["events"]
    return {
        "source": "local_sqlite",
        "configured": result["configured"],
        "limited_to": "first 500 most recent matched records",
        "sample_size": len(rows),
        "total_events": result["total"],
        "aircraft_in_sample": len({row["icao24"] for row in rows}),
        "positions_in_sample": sum(row["latitude"] is not None and row["longitude"] is not None for row in rows),
        "tenants_in_sample": len({row["tenant_id"] for row in rows}),
        "duplicate_ids_in_sample": len(rows) - len({row["event_id"] for row in rows}),
        "last_source_event_at": rows[0]["source_time"] if rows else None,
        "message": result["message"],
    }
