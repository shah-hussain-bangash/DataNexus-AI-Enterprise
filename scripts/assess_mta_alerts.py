"""Phase 3.7: deterministic local MTA alert and recovery decision rules.

Consumes a Phase 3.6 saved JSON snapshot; no network, Kafka commits or
restarts. A snapshot is a point-in-time observation, not a live SLA probe.
"""
import argparse
import json
import sys
from datetime import datetime,timezone
from pathlib import Path

ALLOWED_OFFSETS={"valid","unknown_uncommitted","committed_below_retention","committed_beyond_high_watermark"}
def assess(report,now=None):
    if not isinstance(report,dict) or report.get("state")!="local_monitor_snapshot":
        raise ValueError("Expected saved Phase 3.6 monitor snapshot")
    if report.get("topic")!="mta.subway.updates.v1" or report.get("group")!="datanexus-mta-aggregate-v1":
        raise ValueError("Unexpected MTA topic/group")
    if report.get("production_approved") is not False or report.get("source_api_checked_now") is not False:
        raise ValueError("Untrusted monitoring claims")
    clock=now or datetime.now(timezone.utc)
    if clock.tzinfo is None:raise ValueError("Timezone-aware clock required")
    try:
        stamp=datetime.fromisoformat(report["checked_at_utc"].replace("Z","+00:00"))
        provider=datetime.fromisoformat(report["latest_provider_timestamp_utc"].replace("Z","+00:00"))
    except (KeyError,ValueError,TypeError,AttributeError) as exc:
        raise ValueError("Invalid timestamps") from exc
    if stamp.tzinfo is None or provider.tzinfo is None or stamp>clock or provider>stamp:
        raise ValueError("Future or timezone-naive timestamp")
    age=int((clock-stamp).total_seconds())
    source_age=int((stamp-provider).total_seconds())
    if type(report.get("latest_stored_source_age_seconds")) is not int or abs(report["latest_stored_source_age_seconds"]-source_age)>2:
        raise ValueError("Source age not consistent with snapshot")
    offset=report.get("offset_state")
    lag=report.get("consumer_lag_messages")
    if offset not in ALLOWED_OFFSETS:
        raise ValueError("Invalid offset state")
    if offset=="valid":
        if type(lag)is not int or lag<0:raise ValueError("Lag must be known when offset is valid")
        low,high,committed=(report.get(k) for k in ("low_offset","high_offset_exclusive","committed_next_offset"))
        if not all(type(x)is int for x in (low,high,committed)) or not 0<=low<=committed<=high or lag!=high-committed:
            raise ValueError("Inconsistent Kafka watermark arithmetic")
    elif lag is not None:
        raise ValueError("Unavailable offsets cannot claim known lag")
    alerts=[]
    def add(code,severity,reason,action):
        alerts.append({"code":code,"severity":severity,"reason":reason,"manual_action":action})
    if age>300:
        add("MONITOR_STALE","warning","Saved monitor snapshot is more than five minutes old",
            "Run python scripts/monitor_mta.py --save; do not trust old Kafka lag as current")
    if offset!="valid":
        add("OFFSET_UNKNOWN","critical","Consumer offset state: "+offset,
            "Inspect Kafka topic and consumer group read-only; do not reset offsets automatically")
    elif lag>=10:
        add("CONSUMER_BACKLOG","critical","At least 10 messages pending at snapshot time",
            "Inspect consumer and run one opt-in consume after checking for poison events")
    elif lag>0:
        add("CONSUMER_BACKLOG","warning","Some messages pending at snapshot time",
            "Inspect consumer progress and use opt-in one-message consumer if appropriate")
    if source_age>300:
        add("STORED_OBSERVATION_OLD","warning","Last stored MTA observation was over five minutes old at snapshot time",
            "Check bounded producer/consumer separately; this does not prove MTA outage")
    critical=any(x["severity"]=="critical" for x in alerts)
    return {"state":"local_mta_alert_assessment","assessed_at_utc":clock.isoformat(),
            "snapshot_checked_at_utc":stamp.isoformat(),"snapshot_age_seconds":age,
            "status":"critical" if critical else ("attention" if alerts else "no_threshold_breaches_in_snapshot"),
            "alert_count":len(alerts),"alerts":alerts,
            "automatic_recovery_performed":False,"kafka_offsets_modified":False,
            "production_approved":False,
            "caveat":"Manual advisory only. A clean saved snapshot is not proof of live provider or deployment health."}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file",required=True,help="Phase 3.6 saved monitor JSON")
    parser.add_argument("--strict",action="store_true",help="Return nonzero when any alert exists")
    args=parser.parse_args()
    path=Path(args.file)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>16384:
        raise ValueError("Invalid local monitoring evidence file")
    result=assess(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(result,indent=2))
    if args.strict and result["alert_count"]:sys.exit(2)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("MTA alert assessment failed closed:",str(exc),file=sys.stderr)
        sys.exit(1)
