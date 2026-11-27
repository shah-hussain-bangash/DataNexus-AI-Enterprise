"""Bounded NOAA NCEI daily-summaries weather acquisition for local Power BI.

Opt-in download; fixed official HTTPS service and allowlisted NYC station.
No streaming, fabricated rows, or production approval.
"""
import argparse,hashlib,json,math,urllib.parse,urllib.request
from datetime import date,datetime,timezone
from pathlib import Path

ENDPOINT="https://www.ncei.noaa.gov/access/services/data/v1"
STATION="USW00094728"
ROOT=Path("data/dev/noaa_weather")
FIELDS=("TMAX","TMIN","PRCP")

def url_for(start,end,station=STATION):
    a,b=date.fromisoformat(start),date.fromisoformat(end)
    if station!=STATION or not a<=b or (b-a).days>31 or b>datetime.now(timezone.utc).date():
        raise ValueError("Only a bounded completed date window and approved station permitted")
    return ENDPOINT+"?"+urllib.parse.urlencode({"dataset":"daily-summaries","stations":station,
        "startDate":start,"endDate":end,"dataTypes":",".join(FIELDS),"units":"metric","format":"json"})

def optional_float(v,field):
    if v in (None,""):return None
    if type(v) not in (str,float,int):raise ValueError("Non-numeric NOAA "+field)
    try:n=float(v)
    except ValueError as exc:raise ValueError("Invalid NOAA "+field) from exc
    if not math.isfinite(n):raise ValueError("Nonfinite NOAA "+field)
    minimum,maximum={"TMAX":(-100,65),"TMIN":(-110,60),"PRCP":(0,2000)}[field]
    if not minimum<=n<=maximum:raise ValueError("NOAA "+field+" outside plausible bounds")
    return n

def normalize(payload,start,end):
    if not isinstance(payload,list) or not 0<len(payload)<=32:
        raise ValueError("NOAA response is empty, oversized or not a row list")
    seen=set();out=[]
    for row in payload:
        if not isinstance(row,dict) or not {"DATE","STATION"}.issubset(row):
            raise ValueError("Invalid NOAA daily observation")
        if row["STATION"]!=STATION:raise ValueError("Unexpected NOAA station")
        stamp=row["DATE"]
        if not isinstance(stamp,str):raise ValueError("Invalid date")
        day=date.fromisoformat(stamp[:10])
        if stamp!=day.isoformat() or not start<=stamp<=end or stamp in seen:
            raise ValueError("NOAA date outside window or duplicate")
        seen.add(stamp)
        tmax=optional_float(row.get("TMAX"),"TMAX")
        tmin=optional_float(row.get("TMIN"),"TMIN")
        prcp=optional_float(row.get("PRCP"),"PRCP")
        if tmax is None and tmin is None and prcp is None:
            raise ValueError("All NOAA measurements missing")
        if tmin is not None and tmax is not None and tmin>tmax:
            raise ValueError("NOAA minimum temperature exceeds maximum")
        out.append({"station":STATION,"date":stamp,"tmax_c":tmax,"tmin_c":tmin,"precip_mm":prcp})
    return sorted(out,key=lambda r:r["date"])

def digest(rows):
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def fetch(start,end,folder=ROOT,opener=None):
    url=url_for(start,end);folder=Path(folder)
    stem=f"noaa-daily-{STATION}-{start}-to-{end}"
    snap=folder/(stem+".json");manifest=folder/(stem+".manifest.json")
    if snap.exists() or manifest.exists():raise FileExistsError("Weather snapshot already exists; no overwrite")
    request=urllib.request.Request(url,headers={"User-Agent":"DataNexus-AI-Enterprise/0.1","Accept":"application/json"})
    with (opener or urllib.request.urlopen)(request,timeout=30) as response:
        raw=response.read(1_000_001)
    if len(raw)>1_000_000:raise ValueError("NOAA response exceeds allowed size")
    rows=normalize(json.loads(raw),start,end)
    metadata={"source":"NOAA NCEI daily-summaries","station":STATION,"url":url,
        "start":start,"end":end,"count":len(rows),
        "retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
        "raw_sha256":hashlib.sha256(raw).hexdigest(),"records_sha256":digest(rows),
        "snapshot":snap.name,"units":"metric","continuous":False,"production_approved":False}
    folder.mkdir(parents=True,exist_ok=True)
    try:
        with snap.open("x",encoding="utf-8") as f:json.dump(rows,f,allow_nan=False)
        with manifest.open("x",encoding="utf-8") as f:json.dump(metadata,f,indent=2)
    except Exception:
        if snap.exists():snap.unlink()
        if manifest.exists():manifest.unlink()
        raise
    return {"status":"verified_local_snapshot","records":len(rows),"station":STATION,"manifest":str(manifest)}

def load(folder=ROOT):
    folder=Path(folder)
    manifests=sorted(folder.glob(f"noaa-daily-{STATION}-*.manifest.json"),reverse=True) if folder.is_dir() else []
    if not manifests:return None
    manifest=manifests[0]
    if manifest.is_symlink() or manifest.stat().st_size>12000:raise ValueError("Unsafe NOAA manifest")
    meta=json.loads(manifest.read_text(encoding="utf-8"))
    keys={"source","station","url","start","end","count","retrieved_at_utc",
          "raw_sha256","records_sha256","snapshot","units","continuous","production_approved"}
    if set(meta)!=keys or meta["source"]!="NOAA NCEI daily-summaries" or meta["station"]!=STATION or meta["units"]!="metric" or meta["continuous"] is not False or meta["production_approved"] is not False:
        raise ValueError("Untrusted NOAA metadata")
    if meta["url"]!=url_for(meta["start"],meta["end"]):raise ValueError("Unverified NOAA source query")
    name=f"noaa-daily-{STATION}-{meta['start']}-to-{meta['end']}.json"
    if meta["snapshot"]!=name:raise ValueError("Unexpected NOAA snapshot identity")
    snap=folder/name
    if snap.is_symlink() or not snap.is_file() or snap.stat().st_size>1_000_000:raise ValueError("NOAA snapshot unavailable")
    rows=json.loads(snap.read_text(encoding="utf-8"))
    if type(meta["count"])is not int or len(rows)!=meta["count"] or digest(rows)!=meta["records_sha256"]:
        raise ValueError("NOAA snapshot modified or count mismatch")
    # Revalidate normalized schema and semantic fields rather than trust JSON.
    if any(set(row)!={"station","date","tmax_c","tmin_c","precip_mm"} for row in rows):
        raise ValueError("Unexpected normalized NOAA fields")
    source_rows=[{"STATION":r["station"],"DATE":r["date"],"TMAX":r["tmax_c"],
                  "TMIN":r["tmin_c"],"PRCP":r["precip_mm"]} for r in rows]
    if normalize(source_rows,meta["start"],meta["end"])!=rows:
        raise ValueError("NOAA stored observations inconsistent")
    return {"metadata":meta,"records":rows}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--start",default="2024-01-01")
    p.add_argument("--end",default="2024-01-31")
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    if not args.execute:print(json.dumps({"mode":"plan","url":url_for(args.start,args.end),"writes":False},indent=2))
    else:print(json.dumps(fetch(args.start,args.end),indent=2))
