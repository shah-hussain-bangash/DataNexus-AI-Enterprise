"""Import official EIA-930 six-month BALANCE CSV without an API credential.

Source: https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/
Accept only the official 2024 Jan-Jun BALANCE filename, select PJM hours
January 1-7, 2024, and persist a bounded SHA-256-verified local snapshot.
The operator downloads the CSV separately. Never claim an online fetch here.
"""
import argparse,csv,hashlib,json,math,re
from datetime import datetime,timezone
from pathlib import Path
from ingest_eia_energy import digest

FILENAME="EIA930_BALANCE_2024_Jan_Jun.csv"
URL="https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/"+FILENAME
ROOT=Path("data/dev/eia_energy_bulk")
START="2024-01-01"
END="2024-01-07"
BA="PJM"
LIMIT=168
REQUIRED=("Balancing Authority","UTC Time at End of Hour","Demand (MW)")
STEM="eia930-pjm-demand-2024-01-01-to-2024-01-07"

def parse_stamp(value):
    if not isinstance(value,str):raise ValueError("Missing UTC date")
    try:
        # Official EIA-930 six-month files publish UTC as M/D/YYYY H:MM:SS AM/PM.
        value=value.strip()
        return datetime.strptime(value,"%m/%d/%Y %I:%M:%S %p")
    except ValueError as exc:raise ValueError("Unrecognized EIA-930 UTC timestamp format") from exc

def parse_rows(handle):
    reader=csv.DictReader(handle)
    if not reader.fieldnames or not all(x in reader.fieldnames for x in REQUIRED):
        raise ValueError("Unexpected EIA-930 BALANCE CSV header; import refused")
    seen=set();result=[]
    for row in reader:
        if not isinstance(row,dict) or None in row:raise ValueError("Malformed EIA-930 CSV row")
        if row["Balancing Authority"]!=BA:continue
        dt=parse_stamp(row["UTC Time at End of Hour"])
        day=dt.date().isoformat()
        if not START<=day<=END:continue
        value=row["Demand (MW)"]
        if not isinstance(value,str) or not value.strip() or value.strip().upper() in {"NA","N/A","NULL","-"}:
            # Missing values are not converted to zero.
            continue
        try:demand=float(value.replace(",","").strip())
        except ValueError as exc:raise ValueError("Non-numeric EIA-930 demand") from exc
        if not math.isfinite(demand) or not 0<=demand<=1_000_000:
            raise ValueError("EIA-930 demand outside allowable range")
        stamp=dt.strftime("%Y-%m-%dT%H")
        if stamp in seen:raise ValueError("Duplicate EIA-930 PJM UTC hour")
        seen.add(stamp)
        result.append({"respondent":BA,"date":day,"period_utc":stamp,
            "demand_mwh":demand,"source_unit":"megawatthours",
            "series_type":"D"})
        if len(result)>LIMIT:raise ValueError("More than 168 PJM UTC hourly observations")
    if len(result)<24:raise ValueError("Insufficient verified PJM hourly observations for selected week")
    return sorted(result,key=lambda x:x["period_utc"])

def import_csv(path,folder=ROOT):
    path=Path(path)
    if path.name!=FILENAME or path.is_symlink() or not path.is_file():
        raise ValueError("Select an existing official EIA-930 BALANCE CSV filename")
    if path.stat().st_size>150_000_000:raise ValueError("CSV exceeds 150 MB limit")
    folder=Path(folder);snapshot=folder/(STEM+".json");manifest=folder/(STEM+".manifest.json")
    if snapshot.exists() or manifest.exists():raise FileExistsError("Immutable EIA bulk snapshot already exists")
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    with path.open("r",encoding="utf-8-sig",newline="") as f:records=parse_rows(f)
    meta={"source":"EIA-930 six-month BALANCE CSV","source_url":URL,"input_filename":FILENAME,
        "input_sha256":h.hexdigest(),"respondent":BA,"series":"D","start":START,"end":END,
        "count":len(records),"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
        "records_sha256":digest(records),"snapshot":snapshot.name,
        "continuous":False,"production_approved":False}
    folder.mkdir(parents=True,exist_ok=True)
    try:
        with snapshot.open("x",encoding="utf-8") as f:json.dump(records,f,allow_nan=False)
        with manifest.open("x",encoding="utf-8") as f:json.dump(meta,f,indent=2)
    except Exception:
        snapshot.unlink(missing_ok=True);manifest.unlink(missing_ok=True);raise
    return {"status":"verified_local_snapshot","records":len(records),"respondent":BA,
        "source":"EIA-930 six-month CSV","manifest":str(manifest)}

def load(folder=ROOT):
    folder=Path(folder);manifest=folder/(STEM+".manifest.json");snapshot=folder/(STEM+".json")
    if not manifest.exists():return None
    if manifest.is_symlink() or snapshot.is_symlink() or not snapshot.is_file() or manifest.stat().st_size>12000 or snapshot.stat().st_size>200000:
        raise ValueError("EIA-930 bulk snapshot unsafe or incomplete")
    meta=json.loads(manifest.read_text(encoding="utf-8"))
    keys={"source","source_url","input_filename","input_sha256","respondent","series",
        "start","end","count","retrieved_at_utc","records_sha256","snapshot","continuous","production_approved"}
    if not isinstance(meta,dict) or set(meta)!=keys or meta["source"]!="EIA-930 six-month BALANCE CSV" or meta["source_url"]!=URL or meta["input_filename"]!=FILENAME or meta["respondent"]!=BA or meta["series"]!="D" or meta["start"]!=START or meta["end"]!=END or meta["snapshot"]!=snapshot.name or meta["continuous"] is not False or meta["production_approved"] is not False:
        raise ValueError("EIA-930 bulk manifest untrusted")
    if not isinstance(meta["input_sha256"],str) or not re.fullmatch(r"[0-9a-f]{64}",meta["input_sha256"]):
        raise ValueError("Invalid EIA-930 source SHA-256")
    records=json.loads(snapshot.read_text(encoding="utf-8"))
    if not isinstance(records,list) or type(meta["count"]) is not int or len(records)!=meta["count"] or len(records)<24 or len(records)>LIMIT or digest(records)!=meta["records_sha256"]:
        raise ValueError("EIA-930 bulk record integrity mismatch")
    fields={"respondent","date","period_utc","demand_mwh","source_unit","series_type"}
    seen=set()
    for r in records:
        if not isinstance(r,dict) or set(r)!=fields or r["respondent"]!=BA or r["series_type"]!="D" or r["source_unit"]!="megawatthours" or not START<=r["date"]<=END or not isinstance(r["period_utc"],str) or len(r["period_utc"])!=13 or not r["period_utc"].startswith(r["date"]+"T") or type(r["demand_mwh"]) not in (int,float) or not math.isfinite(r["demand_mwh"]) or not 0<=r["demand_mwh"]<=1_000_000 or r["period_utc"] in seen:
            raise ValueError("Invalid EIA-930 stored row")
        seen.add(r["period_utc"])
    return {"metadata":meta,"records":records}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv",type=Path,help="Previously downloaded official EIA930_BALANCE_2024_Jan_Jun.csv")
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    if not args.execute:
        print(json.dumps({"mode":"plan","file":FILENAME,"source_url":URL,
            "authority":BA,"start":START,"end":END,"requires_api_key":False,
            "network_access":False,"writes":False},indent=2))
    else:
        if args.csv is None:p.error("--csv is required with --execute")
        print(json.dumps(import_csv(args.csv),indent=2))
