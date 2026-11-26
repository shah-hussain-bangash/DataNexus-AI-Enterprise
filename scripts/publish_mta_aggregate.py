"""Phase 3.2: opt-in one-shot MTA aggregate Kafka producer.

Publishes ONE aggregate event per validated GTFS-Realtime response, never
individual passenger/trip/vehicle records. Dry run is the default.
No continuous polling, replay consumer, or production release assertion.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from collect_mta_gtfs import fetch_feed

TOPIC="mta.subway.updates.v1"
BOOTSTRAP="127.0.0.1:19092"

def event_from_evidence(evidence):
    if evidence.get("source")!="mta_nyct_subway_gtfs_rt" or evidence.get("stage")!="local_provider_connectivity_validation_only":
        raise ValueError("Unverified MTA source")
    if evidence.get("freshness_state")!="fresh" or evidence.get("valid_gtfs_entities") is not True:
        raise ValueError("MTA provider data must be fresh and schema-valid")
    feed=evidence.get("feed_id")
    stamp=evidence.get("provider_timestamp_utc")
    digest=evidence.get("response_sha256")
    if feed not in ("ace","1234567") or not isinstance(stamp,str) or not isinstance(digest,str) or len(digest)!=64:
        raise ValueError("Invalid provider provenance")
    for field in ("entities","trip_updates","vehicle_positions","alerts"):
        if type(evidence.get(field))!=int or evidence[field]<0:
            raise ValueError("Invalid aggregate counter: "+field)
    if evidence["entities"]<=0 or any(evidence[f]>evidence["entities"] for f in ("trip_updates","vehicle_positions","alerts")):
        raise ValueError("MTA entity counts out of bounds")
    event_id=hashlib.sha256((feed+"|"+stamp+"|"+digest).encode("utf-8")).hexdigest()
    return {
        "event_id":event_id,"schema_version":"1.0",
        "source":"mta_nyct_subway_gtfs_rt",
        "feed_id":feed,"provider_timestamp_utc":stamp,
        "observed_at_utc":evidence["observed_at_utc"],
        "provider_response_sha256":digest,
        "counts":{name:evidence[name] for name in ("entities","trip_updates","vehicle_positions","alerts")},
        "kind":"one_shot_aggregate","production_approved":False,
    }

def publish_once(event,bootstrap=BOOTSTRAP,producer_factory=None):
    # The broker is localhost development only. No arbitrary topic input is accepted.
    if bootstrap not in ("127.0.0.1:19092","localhost:19092"):
        raise ValueError("Kafka bootstrap must be local Windows loopback")
    if event.get("kind")!="one_shot_aggregate":
        raise ValueError("Only aggregate events permitted")
    if producer_factory is None:
        try:
            from confluent_kafka import Producer
        except ImportError as exc:
            raise RuntimeError("Install: python -m pip install -e '.[kafka]'") from exc
        producer_factory=Producer
    producer=producer_factory({
        "bootstrap.servers":bootstrap,
        "enable.idempotence":True,
        "acks":"all",
        "message.timeout.ms":15000,
        "client.id":"datanexus-mta-once",
    })
    # Fail closed if topic is absent; do not depend on broker topic autocreation.
    metadata=producer.list_topics(timeout=10)
    if TOPIC not in metadata.topics or metadata.topics[TOPIC].error is not None:
        raise RuntimeError("MTA Kafka topic missing or unavailable")
    errors=[]
    receipts=[]
    payload=json.dumps(event,sort_keys=True,separators=(",",":")).encode("utf-8")
    if len(payload)>16384:
        raise ValueError("Aggregate message exceeds 16 KiB")
    def done(err,msg):
        if err: errors.append(str(err))
        else: receipts.append({"partition":msg.partition(),"offset":msg.offset()})
    producer.produce(TOPIC,key=event["event_id"].encode("ascii"),value=payload,on_delivery=done)
    pending=producer.flush(20)
    if pending or errors or len(receipts)!=1:
        raise RuntimeError("MTA Kafka delivery unverified; publication may be ambiguous")
    return receipts[0]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed",choices=("ace","1234567"),default="ace")
    parser.add_argument("--publish",action="store_true",help="Explicitly allow one aggregate Kafka message")
    parser.add_argument("--bootstrap",choices=("127.0.0.1:19092","localhost:19092"),default=BOOTSTRAP)
    args=parser.parse_args()
    evidence=fetch_feed(args.feed)
    event=event_from_evidence(evidence)
    outcome={"mode":"publish" if args.publish else "dry_run","topic":TOPIC,"event_id":event["event_id"],
             "provider_timestamp_utc":event["provider_timestamp_utc"],"counts":event["counts"],
             "message_kind":"aggregate_only","raw_gtfs_stored":False,"continuous_polling":False}
    if args.publish:
        receipt=publish_once(event,args.bootstrap)
        outcome.update({"broker_delivery_verified":True,**receipt})
    else:
        outcome["broker_delivery_verified"]=False
    print(json.dumps(outcome,indent=2))

if __name__=="__main__":
    try:main()
    except Exception as exc:
        # Nonzero exit: never claim success on failed validation or delivery.
        print("MTA one-shot publish aborted:",str(exc),file=sys.stderr)
        sys.exit(1)
