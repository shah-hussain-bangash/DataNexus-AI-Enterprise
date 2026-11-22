"""Deterministic OpenSky state-vector normalization and envelope validation."""
import hashlib
import json
from datetime import datetime, timezone

REQUIRED = {"event_id", "schema_version", "source", "source_event_time", "ingested_at", "tenant_id", "trace_id", "payload"}


def iso_utc(epoch_seconds):
    return datetime.fromtimestamp(epoch_seconds, timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_states(response, tenant_id="demo", collected_at=None):
    """Build stable event IDs. Input is an OpenSky /states/all response."""
    if not isinstance(response, dict) or not isinstance(response.get("time"), int):
        raise ValueError("OpenSky response requires integer time")
    if response.get("states") is None:
        return []
    if not isinstance(response["states"], list):
        raise ValueError("states must be a list")
    collected = collected_at or iso_utc(__import__("time").time())
    result = []
    for row in response["states"]:
        if not isinstance(row, list) or len(row) < 17 or not isinstance(row[0], str):
            continue
        icao = row[0].strip().lower()
        if not icao:
            continue
        sample_time = row[4] if isinstance(row[4], int) and row[4] > 0 else response["time"]
        payload = {
            "icao24": icao,
            "callsign": row[1].strip() if isinstance(row[1], str) else None,
            "longitude": row[5],
            "latitude": row[6],
            "baro_altitude_m": row[7],
            "on_ground": row[8],
            "velocity_mps": row[9],
            "heading_deg": row[10],
            "vertical_rate_mps": row[11],
            "geo_altitude_m": row[13],
            "position_source": row[16],
        }
        digest = hashlib.sha256(json.dumps([icao, sample_time, payload], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        envelope = {
            "event_id": digest,
            "schema_version": "1.0",
            "source": "opensky.states.all",
            "source_event_time": iso_utc(sample_time),
            "ingested_at": collected,
            "tenant_id": tenant_id,
            "trace_id": digest[:32],
            "payload": payload,
        }
        validate_envelope(envelope)
        result.append(envelope)
    return result


def validate_envelope(event):
    if not isinstance(event, dict) or set(event) != REQUIRED:
        raise ValueError("invalid event envelope keys")
    for name in ("event_id", "source", "source_event_time", "ingested_at", "tenant_id", "trace_id"):
        if not isinstance(event[name], str) or not event[name].strip():
            raise ValueError("invalid field: " + name)
    if event["schema_version"] != "1.0" or not isinstance(event["payload"], dict):
        raise ValueError("invalid schema version or payload")
    for name in ("source_event_time", "ingested_at"):
        try:
            datetime.fromisoformat(event[name].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("invalid timestamp: " + name) from exc
    return event
