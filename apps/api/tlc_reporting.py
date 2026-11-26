"""Protected local NYC TLC reporting preview.

Reads bounded derived JSON only, never individual trips. Fail closed on missing
or inconsistent local evidence. Not a production tenant-isolated data service.
"""
import hashlib
import json
import re
from pathlib import Path

def _sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda:stream.read(1048576),b""):
            h.update(part)
    return h.hexdigest()

def read_preview(data_root, requested_month="2024-01"):
    if requested_month!="2024-01":
        raise ValueError("Only 2024-01 local snapshot supported")
    folder=Path(data_root).resolve()/"nyc_tlc"/"silver_gold_2024_01"
    file=folder/"reporting_preview.json"
    transform=folder/"transform_manifest.json"
    gold=folder/"gold_daily_trips.parquet"
    silver=folder/"silver_trips.parquet"
    for path in (file,transform,gold,silver):
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError("Local reporting snapshot unavailable")
    if file.stat().st_size>250000 or transform.stat().st_size>65536:
        raise ValueError("Reporting snapshot size exceeds local safety limit")
    content=json.loads(file.read_text(encoding="utf-8"))
    manifest=json.loads(transform.read_text(encoding="utf-8"))
    if not isinstance(content,dict) or not isinstance(manifest,dict):
        raise ValueError("Malformed local reporting metadata")
    if content.get("stage")!="local_historical_reporting_preview" or manifest.get("stage")!="local_unapproved_silver_gold":
        raise ValueError("Unapproved reporting source state")
    if content.get("source_month")!=requested_month or manifest.get("period")!=requested_month:
        raise ValueError("Reporting period mismatch")
    if content.get("source_sha256")!=manifest.get("source_sha256") or content.get("silver_rows")!=manifest.get("silver_rows"):
        raise ValueError("Reporting source mismatch")
    for name,path in (("gold_sha256",gold),("silver_sha256",silver),("transform_manifest_sha256",transform)):
        if content.get(name)!=_sha(path):
            raise ValueError("Reporting source file modified after export")
    daily=content.get("daily")
    if not isinstance(daily,list) or len(daily)>400:
        raise ValueError("Invalid daily aggregates")
    if any(not isinstance(row,dict) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}",str(row.get("date","")))
           or type(row.get("trip_count"))!=int or row["trip_count"]<0 for row in daily):
        raise ValueError("Invalid reporting row")
    if sum(x["trip_count"] for x in daily)!=content.get("silver_rows"):
        raise ValueError("Reporting total mismatch")
    return content
