"""Opt-in bounded NOAA CO-OPS verified hourly-height acquisition for Power BI.

Only fixed official station 8518750, MLLW, metric and GMT. This is a
historical snapshot, not continuous stream or flood alerting.
"""
import argparse,hashlib,json,math,urllib.parse,urllib.request
from datetime import date,datetime,timezone
from pathlib import Path

ENDPOINT="https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
STATION="8518750"
ROOT=Path("data/dev/noaa_coastal")
DATUM="MLLW"
PRODUCT="hourly_height"

def url_for(start,end):
    a,b=date.fromisoformat(start),date.fromisoformat(end)
    if not a<=b or (b-a).days>30 or b>datetime.now(timezone.utc).date():
        raise ValueError("Expected a bounded completed coastal historical window")
    params={"begin_date":a.strftime("%Y%m%d"),"end_date":b.strftime("%Y%m%d"),
            "station":STATION,"product":PRODUCT,"datum":DATUM,"time_zone":"gmt",
            "units":"metric","application":"DataNexus_AIEducation","format":"json"}
    return ENDPOINT+"?"+urllib.parse.urlencode(params)

def normalize(payload,start,end):
    if not isinstance(payload,dict) or not isinstance(payload.get("metadata"),dict):
        raise ValueError("Invalid NOAA CO-OPS metadata")
    if "error" in payload:raise ValueError("NOAA CO-OPS error response: "+str(payload["error"])[:150])
    meta=payload["metadata"]
    if str(meta.get("id"))!=STATION:raise ValueError("Unexpected NOAA CO-OPS station")
    rows=payload.get("data")
    if not isinstance(rows,list) or not 0<len(rows)<=744:
        raise ValueError("Missing or oversized NOAA CO-OPS hourly observations")
    begin=date.fromisoformat(start);finish=date.fromisoformat(end)
    seen=set();out=[]
    for item in rows:
        if not isinstance(item,dict) or not isinstance(item.get("t"),str):
            raise ValueError("Invalid NOAA coastal observation")
        try:stamp=datetime.strptime(item["t"],"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError as exc:raise ValueError("Invalid GMT observation timestamp") from exc
        if not begin<=stamp.date()<=finish or stamp.minute!=0 or stamp in seen:
            raise ValueError("Duplicate or out-of-range coastal timestamp")
        seen.add(stamp)
        raw=item.get("v")
        try:value=float(raw)
        except (ValueError,TypeError) as exc:raise ValueError("Missing NOAA coastal height") from exc
        if not math.isfinite(value) or not -15<=value<=25:
            raise ValueError("NOAA coastal height outside supported bounds")
        out.append({"station":STATION,"time_utc":stamp.isoformat(),
                    "date":stamp.date().isoformat(),"height_m":value,
                    "datum":DATUM,"product":PRODUCT})
    return sorted(out,key=lambda x:x["time_utc"])

def digest(rows):
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def fetch(start,end,folder=ROOT,opener=None):
    url=url_for(start,end);folder=Path(folder)
    stem=f"coastal-hourly-{STATION}-{start}-to-{end}"
    snap=folder/(stem+".json");manifest=folder/(stem+".manifest.json")
    if snap.exists() or manifest.exists():raise FileExistsError("Snapshot already exists; no overwrite")
    request=urllib.request.Request(url,headers={"User-Agent":"DataNexus-AI-Enterprise/0.1","Accept":"application/json"})
    with (opener or urllib.request.urlopen)(request,timeout=30) as response:raw=response.read(3_000_001)
    if len(raw)>3_000_000:raise ValueError("NOAA coastal response too large")
    rows=normalize(json.loads(raw),start,end)
    metadata={"source":"NOAA CO-OPS verified hourly heights","station":STATION,
              "product":PRODUCT,"datum":DATUM,"units":"metric","time_zone":"gmt",
              "url":url,"start":start,"end":end,"count":len(rows),
              "retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
              "raw_sha256":hashlib.sha256(raw).hexdigest(),"records_sha256":digest(rows),
              "snapshot":snap.name,"continuous":False,"production_approved":False}
    folder.mkdir(parents=True,exist_ok=True)
    try:
        with snap.open("x",encoding="utf-8") as f:json.dump(rows,f,allow_nan=False)
        with manifest.open("x",encoding="utf-8") as f:json.dump(metadata,f,indent=2)
    except Exception:
        if snap.exists():snap.unlink()
        if manifest.exists():manifest.unlink()
        raise
    return {"status":"verified_local_snapshot","records":len(rows),
            "station":STATION,"product":PRODUCT,"manifest":str(manifest)}

def load(folder=ROOT):
    folder=Path(folder)
    files=sorted(folder.glob(f"coastal-hourly-{STATION}-*.manifest.json"),reverse=True) if folder.is_dir() else []
    if not files:return None
    manifest=files[0]
    if manifest.is_symlink() or manifest.stat().st_size>12000:raise ValueError("Invalid coastal manifest")
    meta=json.loads(manifest.read_text(encoding="utf-8"))
    expected={"source","station","product","datum","units","time_zone","url",
              "start","end","count","retrieved_at_utc","raw_sha256",
              "records_sha256","snapshot","continuous","production_approved"}
    if not isinstance(meta,dict) or set(meta)!=expected or meta["source"]!="NOAA CO-OPS verified hourly heights" or meta["station"]!=STATION or meta["product"]!=PRODUCT or meta["datum"]!=DATUM or meta["units"]!="metric" or meta["time_zone"]!="gmt" or meta["continuous"] is not False or meta["production_approved"] is not False:
        raise ValueError("Untrusted coastal manifest")
    if meta["url"]!=url_for(meta["start"],meta["end"]):raise ValueError("Unexpected source URL")
    expected_name=f"coastal-hourly-{STATION}-{meta['start']}-to-{meta['end']}.json"
    if meta["snapshot"]!=expected_name:raise ValueError("Wrong snapshot filename")
    snap=folder/expected_name
    if snap.is_symlink() or not snap.is_file() or snap.stat().st_size>3_000_000:
        raise ValueError("Missing coastal snapshot")
    rows=json.loads(snap.read_text(encoding="utf-8"))
    if not isinstance(rows,list) or type(meta["count"]) is not int or len(rows)!=meta["count"] or digest(rows)!=meta["records_sha256"]:
        raise ValueError("Coastal snapshot checksum or count mismatch")
    replay={"metadata":{"id":STATION},"data":[{"t":datetime.fromisoformat(r["time_utc"]).strftime("%Y-%m-%d %H:%M"),"v":r["height_m"]} for r in rows]}
    if any(set(r)!={"station","time_utc","date","height_m","datum","product"} or r["station"]!=STATION or r["datum"]!=DATUM or r["product"]!=PRODUCT for r in rows) or normalize(replay,meta["start"],meta["end"])!=rows:
        raise ValueError("Coastal observations failed revalidation")
    return {"metadata":meta,"records":rows}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--start",default="2024-01-01")
    p.add_argument("--end",default="2024-01-07")
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    if not args.execute:print(json.dumps({"mode":"plan","url":url_for(args.start,args.end),"writes":False},indent=2))
    else:print(json.dumps(fetch(args.start,args.end),indent=2))
