"""Bounded read-only local MTA aggregate observations (not a live feed)."""
import re
import sqlite3
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path

HEX=re.compile(r"^[a-f0-9]{64}$")

def read_mta_observations(data_root,limit=20):
    if type(limit) is not int or not 1<=limit<=50:
        raise ValueError("Invalid aggregate observation limit")
    path=(Path(data_root).resolve()/"mta"/"mta_aggregate.sqlite3")
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError("Local MTA aggregate store unavailable")
    with closing(sqlite3.connect(path.as_uri()+"?mode=ro",uri=True,timeout=3)) as db:
        db.row_factory=sqlite3.Row
        # Only predeclared fixed columns; never expose raw trip or vehicle identifiers.
        rows=db.execute("""SELECT event_id,provider_timestamp_utc,observed_at_utc,feed_id,
            response_sha256,entities,trip_updates,vehicle_positions,alerts
            FROM mta_aggregates ORDER BY provider_timestamp_utc DESC LIMIT ?""",(limit,)).fetchall()
    if not rows:
        return {"state":"local_mta_aggregate_empty","observations":[],"count":0,
                "live_stream_connected":False,"production_approved":False}
    out=[]
    now=datetime.now(timezone.utc)
    for row in rows:
        item=dict(row)
        if item["feed_id"] not in ("ace","1234567") or not HEX.fullmatch(item["event_id"]) or not HEX.fullmatch(item["response_sha256"]):
            raise ValueError("Local MTA provenance invalid")
        try:
            at=datetime.fromisoformat(item["provider_timestamp_utc"].replace("Z","+00:00"))
            if at.tzinfo is None or at>now:raise ValueError()
        except (ValueError,TypeError,AttributeError) as exc:
            raise ValueError("Invalid MTA source timestamp") from exc
        for key in ("entities","trip_updates","vehicle_positions","alerts"):
            if type(item[key]) is not int or item[key]<0:
                raise ValueError("Invalid MTA aggregate counts")
        if item["entities"]<1 or any(item[k]>item["entities"] for k in ("trip_updates","vehicle_positions","alerts")):
            raise ValueError("MTA counts out of bounds")
        # Explicitly mark freshness of the historical observation, not of the provider now.
        item["observation_age_seconds"]=max(0,int((now-at).total_seconds()))
        out.append(item)
    return {"state":"local_historical_mta_aggregate_observations",
            "observations":out,"count":len(out),"live_stream_connected":False,
            "production_approved":False,
            "caveat":"Local one-shot Kafka consumer records. No continuous source polling, live subscription, or enterprise tenant isolation."}
