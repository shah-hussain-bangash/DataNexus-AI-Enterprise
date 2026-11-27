"""Phase 3.5: bounded, opt-in MTA aggregate pipeline. NOT a daemon.

Default is plan-only, no network access. --execute explicitly enables at most
three sequential MTA API requests and local Kafka publish/consume operations.
"""
import argparse
import json
import sys
import time
from datetime import datetime,timezone

from collect_mta_gtfs import fetch_feed
from publish_mta_aggregate import event_from_evidence,publish_once
from consume_mta_aggregate import consume_once,DB

MIN_INTERVAL=60
MAX_CYCLES=3

def validate_schedule(cycles,interval):
    if type(cycles)!=int or not 1<=cycles<=MAX_CYCLES:
        raise ValueError("Cycles must be 1..3")
    if type(interval)!=int or not MIN_INTERVAL<=interval<=3600:
        raise ValueError("Interval must be 60..3600 seconds")
    return {"cycles":cycles,"interval_seconds":interval,"max_provider_requests":cycles,
            "automatic_retries":False,"daemon":False,"production_approved":False}

def run(cycles=1,interval=120,feed="ace",execute=False,
        fetcher=fetch_feed,publisher=publish_once,consumer=consume_once,
        sleeper=time.sleep):
    plan=validate_schedule(cycles,interval)
    if feed not in ("ace","1234567"):
        raise ValueError("Unsupported MTA feed")
    if not execute:
        return {"state":"plan_only","feed":feed,**plan,"network_requested":False,"kafka_published":False}
    outcomes=[]
    for index in range(cycles):
        if index:
            sleeper(interval)
        # Fetch, validate and publish exactly one aggregate from this request.
        evidence=fetcher(feed)
        event=event_from_evidence(evidence)
        delivery=publisher(event)
        # A consumer may recover an older uncommitted record. Do not present it
        # as a confirmation of this specific published event unless IDs match.
        consumed=consumer(db=DB,timeout_seconds=10)
        same=(consumed.get("event_id")==event["event_id"] and
              consumed.get("offset_committed") is True)
        result={"cycle":index+1,"source_timestamp":event["provider_timestamp_utc"],
                "event_id":event["event_id"],"topic":"mta.subway.updates.v1",
                "broker_delivery_verified":True,
                "partition":delivery["partition"],"offset":delivery["offset"],
                "consumer_state":consumed["state"],
                "consumer_event_matches_publish":same,
                "consumer_offset_committed":consumed.get("offset_committed",False)}
        outcomes.append(result)
        # No silent success on backlog, missing evidence, or consumer failure.
        if not same:
            return {"state":"attention_required","feed":feed,**plan,
                    "completed_cycles":len(outcomes),"observations":outcomes,
                    "caveat":"The consumer did not confirm this cycle's event. Inspect backlog before retrying."}
    return {"state":"bounded_cycle_verified","feed":feed,**plan,
            "completed_cycles":len(outcomes),"observations":outcomes,
            "caveat":"Finite local checks only; not autonomous streaming or production SLA."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--feed",choices=("ace","1234567"),default="ace")
    p.add_argument("--cycles",type=int,default=1)
    p.add_argument("--interval",type=int,default=120)
    p.add_argument("--execute",action="store_true",
                   help="Allow finite API requests, Kafka writes and SQLite commits")
    args=p.parse_args()
    result=run(args.cycles,args.interval,args.feed,args.execute)
    print(json.dumps(result,indent=2))
    if result["state"]=="attention_required":
        sys.exit(2)

if __name__=="__main__":
    try:main()
    except KeyboardInterrupt:
        print("MTA bounded run interrupted by operator",file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print("MTA bounded run aborted:",str(exc),file=sys.stderr)
        sys.exit(1)
