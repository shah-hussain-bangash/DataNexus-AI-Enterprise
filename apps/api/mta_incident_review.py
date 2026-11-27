"""Phase 3.9 local incident review ledger. This is not enterprise authorization.

An operator explicitly records review actions. Immutable assessment files remain
unchanged; resolution is a human assertion requiring a newer evidence reference,
not proof that the underlying MTA condition has recovered.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HEX=re.compile(r"^[a-f0-9]{64}$")
ACTOR=re.compile(r"^[a-zA-Z0-9_.@-]{2,60}$")
STATES={"unreviewed":"acknowledged","acknowledged":"assigned","assigned":"resolved"}
def directory_for(data_root):return Path(data_root).resolve()/"mta"/"incident_reviews"
def assessment_file(data_root,digest):
    if not isinstance(digest,str) or not HEX.fullmatch(digest):
        raise ValueError("Invalid incident evidence digest")
    return Path(data_root).resolve()/"mta"/"alert_history"/("mta-alert-"+digest+".json")
def load_assessment(data_root,digest):
    path=assessment_file(data_root,digest)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>16384:
        raise ValueError("Assessment evidence unavailable")
    obj=json.loads(path.read_text(encoding="utf-8"))
    if obj.get("snapshot_sha256")!=digest or obj.get("incident_lifecycle")!="unreviewed" or obj.get("alert_count",0)<1:
        raise ValueError("Only existing unreviewed alerts may be reviewed")
    return obj
def records(data_root,digest):
    folder=directory_for(data_root)/digest
    if not folder.is_dir():return []
    result=[]
    for path in sorted(folder.glob("*.json")):
        if path.is_symlink() or path.stat().st_size>8192:raise ValueError("Unsafe review record")
        doc=json.loads(path.read_text(encoding="utf-8"))
        if set(doc)!={"schema_version","state","assessment_sha256","sequence","action","actor",
                      "assignee","note","evidence_reference","recorded_at_utc","previous_sha256",
                      "production_approved"} or doc["schema_version"]!="1.0" or doc["state"]!="local_review_action":
            raise ValueError("Invalid review record")
        if doc["assessment_sha256"]!=digest or type(doc["sequence"])is not int or doc["sequence"]!=len(result)+1 or path.name!=f"{doc['sequence']:04d}.json":
            raise ValueError("Invalid review sequence")
        if doc["production_approved"] is not False or not ACTOR.fullmatch(doc["actor"]):
            raise ValueError("Invalid operator identity or approval")
        if doc["action"] not in ("acknowledge","assign","resolve") or not isinstance(doc["note"],str) or not 8<=len(doc["note"])<=500:
            raise ValueError("Invalid incident review action")
        if doc["assignee"] is not None and (not isinstance(doc["assignee"],str) or not ACTOR.fullmatch(doc["assignee"])):
            raise ValueError("Invalid assignee")
        if doc["action"]=="assign" and doc["assignee"] is None:raise ValueError("Assignment requires assignee")
        if doc["action"]=="resolve" and (not isinstance(doc["evidence_reference"],str) or not 12<=len(doc["evidence_reference"])<=200):
            raise ValueError("Resolution requires evidence reference")
        if doc["action"]!="resolve" and doc["evidence_reference"] is not None:
            raise ValueError("Evidence reference only on resolution")
        stamp=datetime.fromisoformat(doc["recorded_at_utc"].replace("Z","+00:00"))
        if stamp.tzinfo is None or stamp>datetime.now(timezone.utc):
            raise ValueError("Future review timestamp")
        expected_action=("acknowledge","assign","resolve")[len(result)] if len(result)<3 else None
        if doc["action"]!=expected_action:raise ValueError("Invalid review state transition")
        previous=hashlib.sha256(json.dumps(result[-1],sort_keys=True,separators=(",",":")).encode()).hexdigest() if result else None
        if doc["previous_sha256"]!=previous:raise ValueError("Review chain broken")
        result.append(doc)
    return result
def append_review(data_root,digest,action,actor,note,assignee=None,evidence_reference=None):
    load_assessment(data_root,digest)
    if action not in ("acknowledge","assign","resolve") or not isinstance(actor,str) or not ACTOR.fullmatch(actor):
        raise ValueError("Invalid review request")
    if not isinstance(note,str) or not 8<=len(note)<=500:raise ValueError("Note must be 8-500 characters")
    if action=="assign" and (not isinstance(assignee,str) or not ACTOR.fullmatch(assignee)):raise ValueError("Assignment requires assignee")
    if action=="resolve" and (not isinstance(evidence_reference,str) or not 12<=len(evidence_reference)<=200):
        raise ValueError("Resolution requires independently obtained evidence reference")
    if action!="resolve" and evidence_reference is not None:raise ValueError("Unexpected resolution evidence")
    if action!="assign" and assignee is not None:raise ValueError("Unexpected assignee")
    old=records(data_root,digest)
    if len(old)>=3 or action!=("acknowledge","assign","resolve")[len(old)]:
        raise ValueError("Review action violates required sequence")
    prior=hashlib.sha256(json.dumps(old[-1],sort_keys=True,separators=(",",":")).encode()).hexdigest() if old else None
    doc={"schema_version":"1.0","state":"local_review_action","assessment_sha256":digest,
         "sequence":len(old)+1,"action":action,"actor":actor,"assignee":assignee,
         "note":note,"evidence_reference":evidence_reference,
         "recorded_at_utc":datetime.now(timezone.utc).isoformat(),
         "previous_sha256":prior,"production_approved":False}
    folder=directory_for(data_root)/digest;folder.mkdir(parents=True,exist_ok=True)
    path=folder/f"{len(old)+1:04d}.json"
    with path.open("x",encoding="utf-8") as target:
        json.dump(doc,target,indent=2,sort_keys=True);target.write("\n")
    return doc
def review_status(data_root,limit=20):
    if type(limit)is not int or not 1<=limit<=50:raise ValueError("Invalid limit")
    folder=Path(data_root).resolve()/"mta"/"alert_history"
    if not folder.is_dir():return {"state":"local_incident_reviews_empty","incidents":[],"count":0,"production_approved":False}
    files=sorted(folder.glob("mta-alert-*.json"),reverse=True)[:limit]
    entries=[]
    for f in files:
        digest=f.name[len("mta-alert-"):-5]
        if not HEX.fullmatch(digest):raise ValueError("Invalid incident filename")
        try:
            assessment=load_assessment(data_root,digest)
        except ValueError:
            # No-action assessments are not actionable incidents.
            if f.is_symlink() or not f.is_file():raise
            evidence=json.loads(f.read_text(encoding="utf-8"))
            if evidence.get("alert_count")==0 and evidence.get("incident_lifecycle")=="not_applicable":continue
            raise
        actions=records(data_root,digest)
        stage=("unreviewed","acknowledged","assigned","resolved")[len(actions)]
        entries.append({"assessment_sha256":digest,"severity":assessment["status"],
                        "alerts":[a["code"] for a in assessment["alerts"]],
                        "review_state":stage,"last_action_utc":actions[-1]["recorded_at_utc"] if actions else None,
                        "assignee":next((a["assignee"] for a in actions if a["action"]=="assign"),None),
                        "resolution_self_reported":stage=="resolved"})
    return {"state":"local_incident_reviews","incidents":entries,"count":len(entries),"production_approved":False,
            "caveat":"Operator claims only. Resolution evidence is a reference, not independent verification or production approval."}
