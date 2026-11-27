"""Phase 3.11 opt-in recovery report from a preserved SQLite backup.

Never alters the source, backup or Kafka; independently checks the backup
integrity and isolated restored row digest before writing report evidence.
"""
import argparse,hashlib,json,os,sqlite3,sys,tempfile
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
from backup_verify_mta import connect_readonly,checksum_rows

def file_sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def verify_existing_backup(path):
    path=Path(path).resolve()
    if not path.name.startswith("mta-recovery-") or path.suffix!=".sqlite3" or not path.is_file() or path.is_symlink() or path.stat().st_size>1_000_000_000:
        raise ValueError("Invalid local MTA recovery backup")
    with closing(connect_readonly(path)) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            raise ValueError("Backup SQLite integrity failed")
        count,digest=checksum_rows(db)
        if not count:raise ValueError("Empty backup")
        with tempfile.TemporaryDirectory(prefix="mta-evidence-") as temp:
            restored=Path(temp)/"restore.sqlite3"
            with closing(sqlite3.connect(restored)) as target:
                db.backup(target)
            with closing(connect_readonly(restored)) as check:
                if check.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                    raise ValueError("Restored SQLite integrity failed")
                recovered_count,recovered_digest=checksum_rows(check)
    if (count,digest)!=(recovered_count,recovered_digest):
        raise ValueError("Restore data mismatch")
    return {"state":"local_mta_recovery_evidence","checked_at_utc":datetime.now(timezone.utc).isoformat(),
            "backup_file_name":path.name,"backup_file_sha256":file_sha256(path),
            "backup_records":count,"restored_records":recovered_count,
            "row_sha256":digest,"sqlite_integrity":"ok","isolated_restore_verified":True,
            "live_source_compared":False,"kafka_recovery_tested":False,"production_approved":False,
            "caveat":"Offline local backup and isolated restore only. Live source, broker recovery and DR objectives not verified."}

def save_report(result,directory):
    directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=True)
    stamp=datetime.fromisoformat(result["checked_at_utc"]).strftime("%Y%m%dT%H%M%S%fZ")
    path=directory/("mta-recovery-report-"+stamp+".json")
    with path.open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    return path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backup",required=True,help="Existing mta-recovery-*.sqlite3 file")
    p.add_argument("--save",action="store_true",help="Save locally auditable JSON evidence")
    p.add_argument("--directory",default="data/dev/mta/recovery_reports")
    a=p.parse_args()
    result=verify_existing_backup(a.backup)
    if a.save:result["saved_report"]=str(save_report(result,a.directory))
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    try:main()
    except Exception as exc:print("MTA recovery report failed:",str(exc),file=sys.stderr);sys.exit(1)
