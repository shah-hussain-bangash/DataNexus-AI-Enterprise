"""Phase 3.3 opt-in one-message MTA Kafka consumer with durable SQLite deduplication.

Consumes from ONLY mta.subway.updates.v1; no continuous loop, no aviation sink.
Offset is committed only after SQLite transaction. No production guarantees.
"""
import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

TOPIC="mta.subway.updates.v1"
GROUP="datanexus-mta-aggregate-v1"
BOOTSTRAP="127.0.0.1:19092"
DB="data/dev/mta/mta_aggregate.sqlite3"
HEX64=re.compile(r"^[a-f0-9]{64}$")
COUNTERS=("entities","trip_updates","vehicle_positions","alerts")

def verify_event(payload):
    if not isinstance(payload,dict):
        raise ValueError("MTA aggregate must be an object")
    required={"event_id","schema_version","source","feed_id","provider_timestamp_utc",
              "observed_at_utc","provider_response_sha256","counts","kind","production_approved"}
    if set(payload)!=required:
        raise ValueError("Unexpected MTA event fields")
    if payload["schema_version"]!="1.0" or payload["source"]!="mta_nyct_subway_gtfs_rt" or payload["kind"]!="one_shot_aggregate" or payload["production_approved"] is not False:
        raise ValueError("Unsupported MTA aggregate schema")
    if payload["feed_id"] not in ("ace","1234567") or not isinstance(payload["event_id"],str) or not HEX64.fullmatch(payload["event_id"]):
        raise ValueError("Invalid MTA event identity")
    if not isinstance(payload["provider_response_sha256"],str) or not HEX64.fullmatch(payload["provider_response_sha256"]):
        raise ValueError("Invalid provider evidence digest")
    for name in ("provider_timestamp_utc","observed_at_utc"):
        try:
            value=datetime.fromisoformat(payload[name].replace("Z","+00:00"))
            if value.tzinfo is None:raise ValueError()
        except (ValueError,AttributeError,TypeError) as exc:
            raise ValueError("Invalid MTA timestamp: "+name) from exc
    counts=payload["counts"]
    if not isinstance(counts,dict) or set(counts)!=set(COUNTERS):
        raise ValueError("Unexpected MTA counts")
    if any(type(counts[key]) is not int or counts[key]<0 for key in COUNTERS):
        raise ValueError("Invalid MTA counters")
    if counts["entities"]<=0 or any(counts[key]>counts["entities"] for key in COUNTERS[1:]):
        raise ValueError("MTA counts exceed entity total")
    return payload

class AggregateStore:
    def __init__(self,path=DB):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.conn=sqlite3.connect(self.path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS mta_aggregates (
            event_id TEXT PRIMARY KEY,
            provider_timestamp_utc TEXT NOT NULL,
            observed_at_utc TEXT NOT NULL,
            feed_id TEXT NOT NULL,
            response_sha256 TEXT NOT NULL,
            entities INTEGER NOT NULL,
            trip_updates INTEGER NOT NULL,
            vehicle_positions INTEGER NOT NULL,
            alerts INTEGER NOT NULL
        )""")
        self.conn.commit()
    def put(self,payload):
        event=verify_event(payload)
        c=event["counts"]
        with self.conn:
            cursor=self.conn.execute("""INSERT OR IGNORE INTO mta_aggregates
                (event_id,provider_timestamp_utc,observed_at_utc,feed_id,response_sha256,
                 entities,trip_updates,vehicle_positions,alerts)
                VALUES (?,?,?,?,?,?,?,?,?)""",(
                event["event_id"],event["provider_timestamp_utc"],event["observed_at_utc"],
                event["feed_id"],event["provider_response_sha256"],
                c["entities"],c["trip_updates"],c["vehicle_positions"],c["alerts"]))
        return cursor.rowcount==1
    def count(self):
        return self.conn.execute("SELECT COUNT(*) FROM mta_aggregates").fetchone()[0]
    def close(self):self.conn.close()

def consume_once(db=DB,bootstrap=BOOTSTRAP,timeout_seconds=10,consumer_factory=None):
    if bootstrap not in ("127.0.0.1:19092","localhost:19092"):
        raise ValueError("Only local Kafka broker allowed")
    if not (1<=timeout_seconds<=30):
        raise ValueError("Timeout must be 1..30 seconds")
    if consumer_factory is None:
        try:
            from confluent_kafka import Consumer
        except ImportError as exc:
            raise RuntimeError("Install: python -m pip install -e '.[kafka]'") from exc
        consumer_factory=Consumer
    consumer=consumer_factory({
        "bootstrap.servers":bootstrap,"group.id":GROUP,
        "auto.offset.reset":"earliest",
        "enable.auto.commit":False,"enable.auto.offset.store":False,
        "client.id":"datanexus-mta-consume-once",
    })
    store=None
    try:
        consumer.subscribe([TOPIC])
        message=consumer.poll(timeout_seconds)
        if message is None:
            return {"state":"no_event_available","topic":TOPIC,"records_in_store":None,"offset_committed":False}
        if message.error():
            raise RuntimeError("Kafka consumer returned error: "+str(message.error()))
        if message.topic()!=TOPIC:
            raise ValueError("Unexpected Kafka topic")
        raw=message.value()
        if not isinstance(raw,bytes) or len(raw)>16384:
            raise ValueError("MTA Kafka message exceeds 16 KiB")
        try:
            event=verify_event(json.loads(raw.decode("utf-8")))
        except (UnicodeError,json.JSONDecodeError) as exc:
            raise ValueError("Malformed MTA event JSON") from exc
        if message.key()!=event["event_id"].encode("ascii"):
            raise ValueError("Kafka key does not match event identity")
        store=AggregateStore(db)
        inserted=store.put(event)
        count=store.count()
        # Never commit poison events or failed DB writes.
        consumer.commit(message=message,asynchronous=False)
        return {"state":"stored" if inserted else "duplicate_already_stored",
                "topic":TOPIC,"event_id":event["event_id"],
                "partition":message.partition(),"offset":message.offset(),
                "records_in_store":count,"offset_committed":True,
                "local_development_only":True}
    finally:
        consumer.close()
        if store is not None:store.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db",default=DB)
    p.add_argument("--bootstrap",choices=("127.0.0.1:19092","localhost:19092"),default=BOOTSTRAP)
    p.add_argument("--timeout",type=int,default=10)
    args=p.parse_args()
    print(json.dumps(consume_once(args.db,args.bootstrap,args.timeout),indent=2))

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("MTA consumer aborted; no intentional offset commit:",exc,file=sys.stderr)
        sys.exit(1)
