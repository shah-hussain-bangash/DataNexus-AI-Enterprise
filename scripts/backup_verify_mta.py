"""Phase 3.10: read-only source SQLite backup and isolated restore verification.

Uses sqlite3 backup API (safe with SQLite WAL) into NEW files, then tests
integrity and row digest on separate restored temp database. Never edits source.
No Kafka calls. Local operator-triggered only.
"""
import argparse
import hashlib
import json
import sqlite3
import sys
import tempfile
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path

DEFAULT_SOURCE=Path("data/dev/mta/mta_aggregate.sqlite3")
DEFAULT_DESTINATION=Path("data/dev/mta/recovery_backups")
COLUMNS=("event_id","provider_timestamp_utc","observed_at_utc","feed_id","response_sha256",
         "entities","trip_updates","vehicle_positions","alerts")
def checksum_rows(conn):
    names={row[1] for row in conn.execute("PRAGMA table_info(mta_aggregates)")}
    if names!=set(COLUMNS):raise ValueError("MTA aggregate schema mismatch")
    rows=conn.execute("SELECT "+",".join(COLUMNS)+" FROM mta_aggregates ORDER BY event_id")
    h=hashlib.sha256();count=0
    for row in rows:
        h.update((json.dumps(row,ensure_ascii=True,separators=(",",":"))+"\n").encode())
        count+=1
    return count,h.hexdigest()
def connect_readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri()+"?mode=ro",uri=True,timeout=5)
def verify_backup(source=DEFAULT_SOURCE,directory=DEFAULT_DESTINATION):
    source=Path(source)
    directory=Path(directory).resolve()
    if source.is_symlink() or not source.is_file() or source.stat().st_size>1_000_000_000:
        raise ValueError("Expected bounded local MTA source database")
    if source.resolve().parent==directory or source.resolve()==directory:
        raise ValueError("Backup location must differ from source")
    directory.mkdir(parents=True,exist_ok=True)
    # Prevent accidental overwrites and keep restoration entirely isolated.
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target=directory/("mta-recovery-"+stamp+".sqlite3")
    if target.exists():raise FileExistsError("Backup destination exists")
    try:
        with closing(connect_readonly(source)) as original:
            if original.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                raise ValueError("Original SQLite integrity check failed")
            source_count,source_digest=checksum_rows(original)
            if source_count==0:raise ValueError("Empty source database cannot demonstrate recovery")
            with closing(sqlite3.connect(target)) as backed:
                original.backup(backed)
                backed.commit()
        with tempfile.TemporaryDirectory(prefix="mta-restore-",dir=directory) as isolated:
            restored=Path(isolated)/"restored.sqlite3"
            with closing(connect_readonly(target)) as saved:
                with closing(sqlite3.connect(restored)) as recovery:
                    saved.backup(recovery)
                    recovery.commit()
            with closing(connect_readonly(restored)) as recovered:
                if recovered.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                    raise ValueError("Restored database integrity failed")
                restored_count,restored_digest=checksum_rows(recovered)
            if (source_count,source_digest)!=(restored_count,restored_digest):
                raise ValueError("Restore record digest differs from source backup")
        return {"state":"local_mta_backup_restore_verified","backup_file":str(target),
                "source_records":source_count,"restored_records":restored_count,
                "row_sha256":source_digest,"sqlite_integrity":"ok","source_modified":False,
                "production_approved":False,
                "caveat":"Consistent SQLite snapshot and isolated restore; not a disaster recovery SLA or broker recovery test."}
    except Exception:
        if target.exists():target.unlink()
        raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true",help="Explicitly create new local backup and verify isolated restore")
    p.add_argument("--source",default=str(DEFAULT_SOURCE))
    p.add_argument("--directory",default=str(DEFAULT_DESTINATION))
    args=p.parse_args()
    if not args.execute:
        print(json.dumps({"state":"plan_only","source":args.source,"destination_directory":args.directory,
                          "writes":"only a newly named backup when --execute",
                          "kafka_mutations":False,"production_approved":False},indent=2))
        return
    print(json.dumps(verify_backup(args.source,args.directory),indent=2))

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("MTA recovery evidence failed:",str(exc),file=sys.stderr)
        sys.exit(1)
