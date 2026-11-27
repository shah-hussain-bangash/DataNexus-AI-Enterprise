"""Phase 3.8: operator-triggered immutable local MTA alert assessment register.

No Kafka I/O, network access, offset changes, or automatically closed incidents.
One record per exact evidence snapshot digest; append-only by exclusive create.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime,timezone
from pathlib import Path

from assess_mta_alerts import assess

MAX_BYTES=16384
REGISTER=Path("data/dev/mta/alert_history")

def register_snapshot(snapshot_path, directory=REGISTER, now=None):
    path=Path(snapshot_path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_BYTES:
        raise ValueError("Expected bounded local Phase 3.6 snapshot")
    raw=path.read_bytes()
    snapshot=json.loads(raw.decode("utf-8"))
    result=assess(snapshot,now=now)
    digest=hashlib.sha256(raw).hexdigest()
    target_dir=Path(directory)
    target_dir.mkdir(parents=True,exist_ok=True)
    target=target_dir/("mta-alert-"+digest+".json")
    # An existing record is never rewritten or falsely marked recovered.
    if target.exists():
        existing=json.loads(target.read_text(encoding="utf-8"))
        if existing.get("snapshot_sha256")!=digest:
            raise ValueError("Existing register entry contradicts evidence digest")
        return target,existing,False
    record={
        "schema_version":"1.0",
        "state":"local_alert_evidence_record",
        "snapshot_sha256":digest,
        "source_snapshot_checked_at_utc":result["snapshot_checked_at_utc"],
        "assessed_at_utc":result["assessed_at_utc"],
        "status":result["status"],
        "alert_count":result["alert_count"],
        "alerts":result["alerts"],
        "incident_lifecycle":"unreviewed" if result["alerts"] else "not_applicable",
        "automatic_recovery_performed":False,
        "production_approved":False,
        "caveat":"Local operator assessment, not an acknowledged incident or production audit."
    }
    # Exclusive atomic create is sufficient for an opt-in local operator register.
    with target.open("x",encoding="utf-8") as out:
        json.dump(record,out,indent=2,sort_keys=True)
        out.write("\n")
    return target,record,True

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file",required=True,help="Saved mta-monitor-*.json snapshot")
    p.add_argument("--output",default=str(REGISTER))
    args=p.parse_args()
    target,record,created=register_snapshot(args.file,args.output)
    print(json.dumps({"history_file":str(target),"created":created,
                      "status":record["status"],"alert_count":record["alert_count"],
                      "incident_lifecycle":record["incident_lifecycle"]},indent=2))

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("MTA alert register failed closed:",str(exc),file=sys.stderr)
        sys.exit(1)
