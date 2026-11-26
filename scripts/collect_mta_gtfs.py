"""Phase 3.1: one-shot MTA subway GTFS-RT connectivity + validation evidence.

Opt-in network call. No Kafka publication, polling loop, or raw GTFS persistence.
Optional dependency: pip install gtfs-realtime-bindings
"""
import argparse
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FEEDS={
    "1234567":"https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "ace":"https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
}
MAX_BYTES=5*1024*1024
MAX_AGE_SECONDS=7200
MAX_FUTURE_SKEW_SECONDS=300

def validate_message(message, now=None):
    """Use decoded GTFS FeedMessage and report aggregate counts, no trip IDs."""
    timestamp=int(message.header.timestamp)
    if timestamp<=0:
        raise ValueError("Missing MTA feed timestamp")
    clock=now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise ValueError("Clock must be timezone-aware")
    age=int(clock.timestamp())-timestamp
    if age < -MAX_FUTURE_SKEW_SECONDS:
        raise ValueError("MTA feed timestamp is too far in future")
    entities=message.entity
    if len(entities)>50000:
        raise ValueError("Unbounded MTA entity count")
    total_trip_updates=0
    total_vehicle_positions=0
    total_alerts=0
    entity_id_set=set()
    duplicate_entities=0
    invalid_entities=0
    for entity in entities:
        identifier=entity.id
        if not isinstance(identifier,str) or not identifier or len(identifier)>256:
            invalid_entities+=1
        if identifier in entity_id_set:
            duplicate_entities+=1
        entity_id_set.add(identifier)
        if entity.HasField("trip_update"):
            total_trip_updates+=1
        if entity.HasField("vehicle"):
            total_vehicle_positions+=1
        if entity.HasField("alert"):
            total_alerts+=1
    if duplicate_entities or invalid_entities:
        raise ValueError("MTA GTFS entity identity validation failed")
    if not entities:
        raise ValueError("MTA feed has no entities to evaluate")
    return {
        "provider_timestamp_utc":datetime.fromtimestamp(timestamp,timezone.utc).isoformat(),
        "provider_age_seconds":age,
        "freshness_state":"fresh" if age<=MAX_AGE_SECONDS else "stale_over_2h",
        "entities":len(entities),
        "trip_updates":total_trip_updates,
        "vehicle_positions":total_vehicle_positions,
        "alerts":total_alerts,
        "duplicate_entity_ids":duplicate_entities,
        "valid_gtfs_entities":True,
    }

def fetch_feed(feed="ace", opener=urllib.request.urlopen, now=None):
    if feed not in FEEDS:
        raise ValueError("Only approved official MTA feed IDs supported")
    try:
        from google.transit import gtfs_realtime_pb2
        from google.protobuf.message import DecodeError
    except ImportError as exc:
        raise RuntimeError("Install optional decoder: python -m pip install gtfs-realtime-bindings") from exc
    url=FEEDS[feed]
    req=urllib.request.Request(url,headers={"Accept":"application/x-protobuf","User-Agent":"DataNexusLocalResearch/0.1"})
    with opener(req,timeout=20) as response:
        final_url=response.geturl() if hasattr(response,"geturl") else url
        if final_url!=url:
            raise ValueError("MTA feed redirected to a different URL")
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            raise ValueError("MTA response exceeds size limit")
        if len(raw)<12:
            raise ValueError("MTA response is empty or truncated")
        status=response.getcode() if hasattr(response,"getcode") else 200
        if status!=200:
            raise ValueError("MTA response status not 200")
    message=gtfs_realtime_pb2.FeedMessage()
    try:
        message.ParseFromString(raw)
    except DecodeError as exc:
        raise ValueError("MTA GTFS-Realtime protobuf invalid") from exc
    if not message.IsInitialized():
        raise ValueError("MTA GTFS-Realtime protobuf lacks required fields")
    observed=now or datetime.now(timezone.utc)
    metrics=validate_message(message,observed)
    return {
        "source":"mta_nyct_subway_gtfs_rt",
        "feed_id":feed,
        "url":url,
        "observed_at_utc":observed.isoformat(),
        "response_sha256":hashlib.sha256(raw).hexdigest(),
        "response_bytes":len(raw),
        **metrics,
        "stage":"local_provider_connectivity_validation_only",
        "kafka_published":False,
        "raw_payload_stored":False,
        "license_review":"pending",
        "production_approved":False,
        "caveat":"One observed provider response, not proof of continuous streaming or an accepted production feed.",
    }

def collect_once(feed="ace", output_dir="data/dev/mta/live_checks"):
    report=fetch_feed(feed)
    directory=Path(output_dir).resolve()
    directory.mkdir(parents=True,exist_ok=True)
    # No overwrite, including repeated checks for the same second.
    observed=datetime.fromisoformat(report["observed_at_utc"])
    dest=directory/("mta_"+feed+"_"+observed.strftime("%Y%m%dT%H%M%S%fZ")+".json")
    if dest.exists():
        raise FileExistsError("Local MTA evidence already exists")
    fd,temp=tempfile.mkstemp(prefix=".mta-check-",dir=directory,text=True)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as out:
            json.dump(report,out,sort_keys=True,indent=2)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp,dest)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return dest,report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed",choices=sorted(FEEDS),default="ace")
    parser.add_argument("--output",default="data/dev/mta/live_checks")
    args=parser.parse_args()
    file,report=collect_once(args.feed,args.output)
    print(json.dumps({"local_evidence_file":str(file),**report},indent=2))

if __name__=="__main__":
    main()
