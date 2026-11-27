"""Phase 3.11 authenticated read-only recovery-evidence inspection."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
SHA=re.compile(r"^[a-f0-9]{64}$")
NAME=re.compile(r"^mta-recovery-\d{8}T\d{12}Z\.sqlite3$")
def latest_recovery(data_root,now=None):
    root=Path(data_root).resolve()/"mta"
    folder=root/"recovery_reports"
    empty={"state":"local_recovery_evidence_unavailable","report":None,"production_approved":False,
           "caveat":"No operator-saved recovery report; a backup file alone is not evidence of a current recovery check."}
    if not folder.is_dir():return empty
    files=sorted(folder.glob("mta-recovery-report-*.json"),reverse=True)
    if not files:return empty
    file=files[0]
    if file.is_symlink() or file.stat().st_size>8192:raise ValueError("Unsafe recovery report")
    report=json.loads(file.read_text(encoding="utf-8"))
    expected={"state","checked_at_utc","backup_file_name","backup_file_sha256",
              "backup_records","restored_records","row_sha256","sqlite_integrity",
              "isolated_restore_verified","live_source_compared","kafka_recovery_tested",
              "production_approved","caveat"}
    if set(report)!=expected or report["state"]!="local_mta_recovery_evidence":
        raise ValueError("Unexpected recovery evidence contract")
    if not NAME.fullmatch(report["backup_file_name"]):
        raise ValueError("Invalid backup name")
    for field in ("backup_file_sha256","row_sha256"):
        if not isinstance(report[field],str) or not SHA.fullmatch(report[field]):
            raise ValueError("Invalid checksum")
    if any(type(report[k])is not int or report[k]<=0 for k in ("backup_records","restored_records")) or report["backup_records"]!=report["restored_records"]:
        raise ValueError("Record count mismatch")
    if report["sqlite_integrity"]!="ok" or report["isolated_restore_verified"] is not True or any(report[k] is not False for k in ("live_source_compared","kafka_recovery_tested","production_approved")):
        raise ValueError("Misleading recovery claims")
    clock=now or datetime.now(timezone.utc)
    checked=datetime.fromisoformat(report["checked_at_utc"].replace("Z","+00:00"))
    if checked.tzinfo is None or checked>clock:raise ValueError("Future recovery report timestamp")
    backup=root/"recovery_backups"/report["backup_file_name"]
    if backup.is_symlink() or not backup.is_file() or backup.stat().st_size>1_000_000_000:
        raise ValueError("Referenced recovery backup is unavailable")
    sha=hashlib.sha256()
    with backup.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):sha.update(chunk)
    if sha.hexdigest()!=report["backup_file_sha256"]:
        raise ValueError("Backup changed since evidence verification")
    age=int((clock-checked).total_seconds())
    return {"state":"local_recovery_evidence","report":{**report,"report_age_seconds":age,
            "report_stale":age>86400,"backup_integrity_digest_matches":True},
            "production_approved":False,
            "caveat":"Read-only file hash and saved isolated-restore evidence; backup integrity is not a live disaster recovery exercise."}
