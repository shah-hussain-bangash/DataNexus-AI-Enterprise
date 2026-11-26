"""Build a bounded read-only JSON reporting snapshot from local Gold Parquet.

Not a production reporting publication. Run after a completed Phase 2.2 local transform.
"""
import argparse
import hashlib
import json
import math
import os
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def build_snapshot(root, target=None):
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Install optional pyarrow to export Gold reporting") from exc
    root=Path(root).resolve()
    meta_path=root/"transform_manifest.json"
    gold_path=root/"gold_daily_trips.parquet"
    silver_path=root/"silver_trips.parquet"
    quarantine_path=root/"rejected_row_reasons.jsonl"
    for path in (meta_path,gold_path,silver_path,quarantine_path):
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing Phase 2.2 source artifact: "+path.name)
    if meta_path.stat().st_size>65536:
        raise ValueError("Unbounded transform manifest")
    meta=json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("stage")!="local_unapproved_silver_gold" or meta.get("source")!="nyc_tlc_yellow_taxi":
        raise ValueError("Not a supported local transform")
    month=meta.get("period")
    if not isinstance(month,str) or len(month)!=7 or month[4]!="-":
        raise ValueError("Invalid reporting month")
    total=meta.get("validated_source_rows")
    accepted=meta.get("silver_rows")
    rejected=meta.get("quarantined_rows")
    if any(type(v)!=int or v<0 for v in (total,accepted,rejected)) or accepted+rejected!=total:
        raise ValueError("Source counts do not reconcile")
    if pq.read_metadata(silver_path).num_rows!=accepted:
        raise ValueError("Silver row count does not reconcile")
    gold=pq.read_table(gold_path)
    expected={"pickup_date","trip_count","trip_distance_sum","total_amount_sum"}
    if not expected.issubset(gold.column_names):
        raise ValueError("Missing Gold reporting columns")
    if gold.num_rows!=meta.get("gold_days") or gold.num_rows>400:
        raise ValueError("Gold date count out of bounds")
    rows=[]
    seen=set()
    for item in gold.select(sorted(expected)).to_pylist():
        day=item["pickup_date"]
        if not isinstance(day,date) or day.isoformat() in seen:
            raise ValueError("Invalid or duplicated Gold date")
        seen.add(day.isoformat())
        count=item["trip_count"]
        distance=item["trip_distance_sum"]
        amount=item["total_amount_sum"]
        if type(count)!=int or count<0 or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in (distance,amount)):
            raise ValueError("Invalid Gold metrics")
        rows.append({"date":day.isoformat(),"trip_count":count,
                     "distance_sum":round(float(distance),2),"total_amount_sum":round(float(amount),2),
                     "within_source_month":day.isoformat().startswith(month+"-")})
    if sum(row["trip_count"] for row in rows)!=accepted:
        raise ValueError("Gold aggregate trip count does not reconcile")
    rows.sort(key=lambda x:x["date"])
    in_scope=[r for r in rows if r["within_source_month"]]
    out_scope=[r for r in rows if not r["within_source_month"]]
    result={
        "stage":"local_historical_reporting_preview",
        "source":"nyc_tlc_yellow_taxi","source_month":month,
        "source_sha256":meta["source_sha256"],
        "gold_sha256":digest(gold_path),
        "silver_sha256":digest(silver_path),
        "transform_manifest_sha256":digest(meta_path),
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "validated_source_rows":total,"silver_rows":accepted,"quarantined_rows":rejected,
        "all_dates_count":len(rows),"in_month_days":len(in_scope),"outside_month_days":len(out_scope),
        "in_month_trip_count":sum(r["trip_count"] for r in in_scope),
        "outside_month_trip_count":sum(r["trip_count"] for r in out_scope),
        "approved_snapshot":None,"published_reporting":False,"license_review":"pending",
        "daily":rows,
        "caveat":"Local development snapshot, not live data, licensed distribution, or a production service.",
    }
    target=Path(target).resolve() if target else root/"reporting_preview.json"
    if target.exists():
        raise FileExistsError("Reporting preview exists; review it before replacement")
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".report-preview-",dir=target.parent,text=True)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            json.dump(result,stream,indent=2,sort_keys=True)
            stream.write("\n")
            stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",default="data/dev/nyc_tlc/silver_gold_2024_01")
    p.add_argument("--output",default=None)
    args=p.parse_args()
    snapshot=build_snapshot(args.input,args.output)
    print(json.dumps({k:v for k,v in snapshot.items() if k!="daily"},indent=2))
