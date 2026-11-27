"""Read-only local MTA alert history, limited to verified operator evidence."""
import json
import re
from datetime import datetime,timezone
from pathlib import Path

HEX=re.compile(r"^[a-f0-9]{64}$")
ALLOWED_CODES={"MONITOR_STALE","OFFSET_UNKNOWN","CONSUMER_BACKLOG","STORED_OBSERVATION_OLD"}
def read_alert_history(data_root,limit=20):
    if type(limit)is not int or not 1<=limit<=50:raise ValueError("Invalid limit")
    folder=Path(data_root).resolve()/"mta"/"alert_history"
    if not folder.is_dir():
        return {"state":"local_alert_history_empty","entries":[],"count":0,"production_approved":False,
                "caveat":"No operator-recorded assessments; missing history is not a clean bill of health."}
    files=sorted(folder.glob("mta-alert-*.json"),key=lambda x:x.name,reverse=True)
    # Bounded read, no traversal through symlinks, no large records.
    entries=[]
    for file in files[:limit]:
        if file.is_symlink() or file.stat().st_size>16384:raise ValueError("Unsafe alert history entry")
        data=json.loads(file.read_text(encoding="utf-8"))
        required={"schema_version","state","snapshot_sha256","source_snapshot_checked_at_utc",
                  "assessed_at_utc","status","alert_count","alerts","incident_lifecycle",
                  "automatic_recovery_performed","production_approved","caveat"}
        if set(data)!=required or data["schema_version"]!="1.0" or data["state"]!="local_alert_evidence_record":
            raise ValueError("Invalid register contract")
        if not isinstance(data["snapshot_sha256"],str) or not HEX.fullmatch(data["snapshot_sha256"]) or file.stem!="mta-alert-"+data["snapshot_sha256"]:
            raise ValueError("Invalid register provenance")
        if data["production_approved"] is not False or data["automatic_recovery_performed"] is not False:
            raise ValueError("Untrusted automated recovery claim")
        if not isinstance(data["alerts"],list) or len(data["alerts"])>4 or type(data["alert_count"])is not int or data["alert_count"]!=len(data["alerts"]):
            raise ValueError("Invalid alert count")
        for alert in data["alerts"]:
            if not isinstance(alert,dict) or set(alert)!={"code","severity","reason","manual_action"} or alert["code"] not in ALLOWED_CODES or alert["severity"] not in ("warning","critical"):
                raise ValueError("Invalid alert details")
            if any(not isinstance(alert[k],str) or len(alert[k])>500 for k in alert):raise ValueError("Invalid alert text")
        expected="critical" if any(x["severity"]=="critical" for x in data["alerts"]) else ("attention" if data["alerts"] else "no_threshold_breaches_in_snapshot")
        if data["status"]!=expected or data["incident_lifecycle"]!=("unreviewed" if data["alerts"] else "not_applicable"):
            raise ValueError("Contradictory incident status")
        now=datetime.now(timezone.utc)
        for key in ("assessed_at_utc","source_snapshot_checked_at_utc"):
            moment=datetime.fromisoformat(data[key].replace("Z","+00:00"))
            if moment.tzinfo is None or moment>now:raise ValueError("Invalid alert timestamp")
        entries.append(data)
    entries.sort(key=lambda x:x["assessed_at_utc"],reverse=True)
    return {"state":"local_alert_history","entries":entries,"count":len(entries),
            "production_approved":False,
            "caveat":"Operator-triggered snapshots only. Unreviewed alerts are not acknowledged or resolved incidents."}
