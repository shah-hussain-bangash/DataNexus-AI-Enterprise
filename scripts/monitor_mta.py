"""Phase 3.6: opt-in read-only Kafka lag and persisted MTA freshness evidence.

Does not create topics, consume records, commit offsets, call MTA or modify data.
Writes a new JSON monitoring snapshot ONLY with --save.
"""
import argparse
import json
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

TOPIC="mta.subway.updates.v1"
GROUP="datanexus-mta-aggregate-v1"
DB=Path("data/dev/mta/mta_aggregate.sqlite3")
OUT=Path("data/dev/mta/monitor_checks")

def snapshot(bootstrap="127.0.0.1:19092",db_path=DB,consumer_factory=None,partition_factory=None,clock=None):
    if bootstrap not in ("127.0.0.1:19092","localhost:19092"):
        raise ValueError("Only local Redpanda bootstrap supported")
    if consumer_factory is None:
        try:
            from confluent_kafka import Consumer,TopicPartition
        except ImportError as exc:
            raise RuntimeError("Install python -m pip install -e '.[kafka]'") from exc
        consumer_factory,partition_factory=Consumer,TopicPartition
    if partition_factory is None:
        raise ValueError("Partition factory required for tests")
    now=clock or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("Clock requires timezone")
    path=Path(db_path)
    if not path.is_file():
        raise FileNotFoundError("MTA SQLite store missing; no metrics fabricated")
    with closing(sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True,timeout=3)) as db:
        row=db.execute("SELECT COUNT(*),MAX(provider_timestamp_utc) FROM mta_aggregates").fetchone()
    count,last=row
    if not count or last is None:
        raise ValueError("MTA store has no processed observations")
    try:
        observed=datetime.fromisoformat(last.replace("Z","+00:00"))
        if observed.tzinfo is None or observed>now:raise ValueError()
    except (ValueError,AttributeError) as exc:
        raise ValueError("Invalid stored provider timestamp") from exc
    age=max(0,int((now-observed).total_seconds()))
    client=consumer_factory({"bootstrap.servers":bootstrap,"group.id":GROUP,
                             "enable.auto.commit":False,"client.id":"datanexus-mta-monitor"})
    try:
        metadata=client.list_topics(topic=TOPIC,timeout=10)
        topic=metadata.topics.get(TOPIC)
        if topic is None or topic.error is not None or set(topic.partitions)!={0}:
            raise RuntimeError("Expected dedicated single-partition MTA topic missing")
        tp=partition_factory(TOPIC,0)
        low,high=client.get_watermark_offsets(tp,timeout=10,cached=False)
        offset=client.committed([tp],timeout=10)[0].offset
        if not (isinstance(low,int) and isinstance(high,int) and 0<=low<=high):
            raise RuntimeError("Kafka watermark invalid")
        # Kafka OFFSET_INVALID (<0) must not be mistaken for zero lag.
        if offset<0:
            lag=None
            offset_state="unknown_uncommitted"
        elif offset<low:
            lag=None
            offset_state="committed_below_retention"
        elif offset>high:
            lag=None
            offset_state="committed_beyond_high_watermark"
        else:
            lag=high-offset
            offset_state="valid"
    finally:
        client.close()
    return {
        "state":"local_monitor_snapshot",
        "checked_at_utc":now.isoformat(),
        "topic":TOPIC,"group":GROUP,"partition":0,
        "low_offset":low,"high_offset_exclusive":high,
        "committed_next_offset":offset if offset>=0 else None,
        "consumer_lag_messages":lag,"offset_state":offset_state,
        "stored_aggregate_records":count,
        "latest_provider_timestamp_utc":observed.isoformat(),
        "latest_stored_source_age_seconds":age,
        "latest_stored_source_age_state":"recent_under_5_min" if age<=300 else "older_than_5_min",
        "source_api_checked_now":False,
        "production_approved":False,
        "caveat":"Operator-triggered local snapshot. Source age is age of last STORED observation, not provider health or continuous streaming uptime."
    }

def save_new(report,directory=OUT):
    directory=Path(directory).resolve()
    directory.mkdir(parents=True,exist_ok=True)
    when=datetime.fromisoformat(report["checked_at_utc"])
    target=directory/("mta-monitor-"+when.strftime("%Y%m%dT%H%M%S%fZ")+".json")
    if target.exists():raise FileExistsError("Monitoring snapshot exists; no overwrite")
    fd,tmp=tempfile.mkstemp(prefix=".mta-monitor-",dir=directory)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as out:
            json.dump(report,out,indent=2,sort_keys=True)
            out.write("\n");out.flush();os.fsync(out.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return target

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bootstrap",choices=("127.0.0.1:19092","localhost:19092"),default="127.0.0.1:19092")
    p.add_argument("--save",action="store_true",help="Save a new local evidence snapshot; never overwrite")
    args=p.parse_args()
    report=snapshot(bootstrap=args.bootstrap)
    if args.save:report["saved_file"]=str(save_new(report))
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("MTA monitoring failed:",str(exc),file=sys.stderr)
        sys.exit(1)
