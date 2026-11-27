"""Phase 3.12: explicit isolated broker restart check (no restart automation).

Requires separate Docker Compose lab on localhost:29092. Creates one fixed
test-only topic, publishes synthetic events, checks committed offset and
persistence across an operator-performed restart. No MTA provider calls.
"""
import argparse,hashlib,json,sys,time
from datetime import datetime,timezone
from pathlib import Path

BOOTSTRAP="127.0.0.1:29092"
TOPIC="datanexus.mta.restart.lab.v1"
GROUP="datanexus-mta-restart-lab-v1"
STATE=Path("data/dev/mta/restart_lab/phase-3-12-state.json")
def make_payload(label):
    return json.dumps({"kind":"isolated_restart_lab","version":1,"label":label,
                       "synthetic":True,"production_approved":False},
                      sort_keys=True,separators=(",",":")).encode()
def validate_record(raw):
    data=json.loads(raw.decode())
    if set(data)!={"kind","version","label","synthetic","production_approved"} or data["kind"]!="isolated_restart_lab" or data["version"]!=1 or data["synthetic"] is not True or data["production_approved"] is not False or data["label"] not in ("before","after"):
        raise ValueError("Unexpected lab record")
    return data
def validate_state(data):
    required={"state","topic","group","bootstrap","pre_record_sha256","prepared_at_utc","pre_offset","pre_committed_next"}
    if not isinstance(data,dict) or set(data)!=required or data["state"]!="prepared" or data["topic"]!=TOPIC or data["group"]!=GROUP or data["bootstrap"]!=BOOTSTRAP or data["pre_offset"]!=0 or data["pre_committed_next"]!=1 or data["pre_record_sha256"]!=hashlib.sha256(make_payload("before")).hexdigest():
        raise ValueError("Invalid prepared state")
    stamp=datetime.fromisoformat(data["prepared_at_utc"])
    if stamp.tzinfo is None or stamp>datetime.now(timezone.utc):raise ValueError("Invalid prepared timestamp")
    return data
def state_file(path):
    path=Path(path)
    if path.is_symlink() or path.exists() and not path.is_file():raise ValueError("Unsafe lab state path")
    return path
def kafka():
    try:
        from confluent_kafka import Consumer,Producer,TopicPartition
        from confluent_kafka.admin import AdminClient,NewTopic
    except ImportError as exc:raise RuntimeError("Install Kafka client with python -m pip install -e '.[kafka]'") from exc
    return Consumer,Producer,TopicPartition,AdminClient,NewTopic
def client_config():
    return {"bootstrap.servers":BOOTSTRAP,"socket.timeout.ms":5000}
def publish(Producer,raw):
    receipts=[]
    errors=[]
    producer=Producer({**client_config(),"acks":"all","enable.idempotence":True,"message.timeout.ms":15000})
    producer.produce(TOPIC,key=b"phase-3-12",value=raw,on_delivery=lambda err,msg: errors.append(str(err)) if err else receipts.append((msg.partition(),msg.offset())))
    pending=producer.flush(20)
    if pending or errors or len(receipts)!=1:raise RuntimeError("Isolated Kafka delivery not verified")
    return receipts[0]
def offset_for(Consumer,TP):
    consumer=Consumer({**client_config(),"group.id":GROUP,"enable.auto.commit":False,"auto.offset.reset":"earliest"})
    try:
        return consumer.committed([TP(TOPIC,0)],timeout=10)[0].offset
    finally:consumer.close()
def get_record(Consumer,TP,index):
    consumer=Consumer({**client_config(),"group.id":"datanexus-mta-restart-lab-inspection-v1",
                       "enable.auto.commit":False,"auto.offset.reset":"earliest"})
    try:
        consumer.assign([TP(TOPIC,0,index)])
        limit=time.monotonic()+12
        while time.monotonic()<limit:
            message=consumer.poll(1)
            if message is None:continue
            if message.error():raise RuntimeError("Lab broker read error: "+str(message.error()))
            if message.topic()!=TOPIC or message.partition()!=0 or message.offset()!=index:
                raise ValueError("Unexpected broker offset or topic")
            if message.key()!=b"phase-3-12":raise ValueError("Unexpected lab key")
            validate_record(message.value())
            return message
        raise TimeoutError("Expected test record unavailable")
    finally:consumer.close()
def prepare(path=STATE):
    path=state_file(path)
    if path.exists():raise FileExistsError("Lab already prepared; do not overwrite the previous run")
    Consumer,Producer,TP,Admin,NewTopic=kafka()
    admin=Admin(client_config())
    # A pre-existing topic is not reset or deleted.
    metadata=admin.list_topics(timeout=10)
    if TOPIC in metadata.topics:
        raise RuntimeError("Lab topic already exists; refuse to reinitialize existing evidence")
    futures=admin.create_topics([NewTopic(TOPIC,num_partitions=1,replication_factor=1)])
    futures[TOPIC].result(timeout=15)
    payload=make_payload("before")
    partition,offset=publish(Producer,payload)
    if (partition,offset)!=(0,0):raise ValueError("Expected fresh isolated topic at offset 0")
    consumer=Consumer({**client_config(),"group.id":GROUP,"enable.auto.commit":False,
                       "enable.auto.offset.store":False,"auto.offset.reset":"earliest"})
    try:
        consumer.subscribe([TOPIC])
        limit=time.monotonic()+15
        while time.monotonic()<limit:
            message=consumer.poll(1)
            if message is None:continue
            if message.error():raise RuntimeError("Lab consumer error: "+str(message.error()))
            if message.offset()!=0 or message.value()!=payload:raise ValueError("Unmatched pre-restart event")
            consumer.commit(message=message,asynchronous=False)
            break
        else:raise TimeoutError("Pre-restart event could not be consumed")
    finally:consumer.close()
    next_offset=offset_for(Consumer,TP)
    if next_offset!=1:raise ValueError("Pre-restart group offset not durably committed")
    state={"state":"prepared","topic":TOPIC,"group":GROUP,"bootstrap":BOOTSTRAP,
           "pre_record_sha256":hashlib.sha256(payload).hexdigest(),
           "prepared_at_utc":datetime.now(timezone.utc).isoformat(),
           "pre_offset":0,"pre_committed_next":next_offset}
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as output:json.dump(state,output,indent=2)
    return {"state":"awaiting_operator_restart","lab_only":True,"topic":TOPIC,
            "pre_offset":0,"pre_committed_next":1,"state_file":str(path),
            "production_approved":False,
            "next_step":"Run explicit docker compose -f docker-compose.mta-restart-lab.yml restart redpanda-lab"}
def verify(path=STATE):
    path=state_file(path)
    if not path.is_file() or path.stat().st_size>8192:raise ValueError("Missing prepared lab state")
    saved=validate_state(json.loads(path.read_text(encoding="utf-8")))
    Consumer,Producer,TP,Admin,NewTopic=kafka()
    start=time.monotonic()
    metadata=Admin(client_config()).list_topics(topic=TOPIC,timeout=10)
    if TOPIC not in metadata.topics or metadata.topics[TOPIC].error is not None:raise RuntimeError("Isolated topic unavailable")
    connect_seconds=round(time.monotonic()-start,3)
    after_restart_committed=offset_for(Consumer,TP)
    if after_restart_committed!=1:raise ValueError("Consumer group committed offset was not retained")
    before=get_record(Consumer,TP,0)
    if hashlib.sha256(before.value()).hexdigest()!=saved["pre_record_sha256"]:raise ValueError("Pre-restart record differs")
    partition,after_offset=publish(Producer,make_payload("after"))
    if (partition,after_offset)!=(0,1):raise ValueError("Post-restart offset continuity lost")
    returned=get_record(Consumer,TP,1)
    if returned.value()!=make_payload("after"):raise ValueError("Post-restart message differs")
    # A read-only inspection does not commit any consumer group offsets.
    if offset_for(Consumer,TP)!=1:raise ValueError("Inspectors unexpectedly modified group offset")
    return {"state":"isolated_restart_lab_verified","lab_only":True,"topic":TOPIC,"group":GROUP,
            "before_offset":0,"after_offset":1,"committed_next_offset":1,
            "pre_restart_record_persisted":True,"post_restart_record_verified":True,
            "group_offset_retained":True,"metadata_connection_seconds":connect_seconds,
            "restart_performed_by_operator_not_attested":True,
            "production_approved":False,
            "caveat":"Operator must verify restart occurred. Connection check time is NOT broker downtime or recovery RTO."}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase",choices=("plan","prepare","verify"),default="plan")
    p.add_argument("--state-file",default=str(STATE))
    args=p.parse_args()
    if args.phase=="plan":
        result={"state":"plan_only","broker":BOOTSTRAP,"topic":TOPIC,"group":GROUP,
                "changes_live_mta":False,"production_approved":False}
    elif args.phase=="prepare":result=prepare(args.state_file)
    else:result=verify(args.state_file)
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("Isolated restart lab failed closed:",str(exc),file=sys.stderr);sys.exit(1)
