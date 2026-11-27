"""USGS modern Water Data API: bounded daily mean streamflow acquisition.

Fixed site USGS-01491000, parameter 00060 (discharge), statistic 00003
(daily mean). Uses modern OGC API v0. No automatic polling or synthetic data.
"""
import argparse,hashlib,json,math,urllib.parse,urllib.request
from datetime import date,datetime,timezone
from pathlib import Path

ENDPOINT="https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items"
SITE="USGS-01491000"
PARAMETER="00060"
STATISTIC="00003"
ROOT=Path("data/dev/usgs_river")
MAX_RESULTS=100

def url_for(start,end):
    a,b=date.fromisoformat(start),date.fromisoformat(end)
    if not a<=b or (b-a).days>30 or b>datetime.now(timezone.utc).date():
        raise ValueError("Only a completed 31-day-or-shorter daily historical window is allowed")
    return ENDPOINT+"?"+urllib.parse.urlencode({
        "f":"json","monitoring_location_id":SITE,"parameter_code":PARAMETER,
        "statistic_id":STATISTIC,"datetime":start+"/"+end,"limit":MAX_RESULTS})

def digest(rows):
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def normalize(payload,start,end):
    if not isinstance(payload,dict) or payload.get("type")!="FeatureCollection" or not isinstance(payload.get("features"),list):
        raise ValueError("Unrecognized USGS daily-values response")
    features=payload["features"]
    if not 0<len(features)<MAX_RESULTS:raise ValueError("Empty or unexpectedly large USGS river response")
    returned=payload.get("numberReturned")
    matched=payload.get("numberMatched")
    if returned is not None and (type(returned)is not int or returned!=len(features)):
        raise ValueError("USGS numberReturned does not match features")
    if matched is not None and (type(matched)is not int or matched>len(features)):
        raise ValueError("USGS data pagination detected: narrow the date window")
    if any(isinstance(link,dict) and link.get("rel")=="next" for link in payload.get("links",[])):
        raise ValueError("USGS response has an unprocessed next page")
    seen=set();rows=[]
    for feature in features:
        if not isinstance(feature,dict) or feature.get("type")!="Feature" or not isinstance(feature.get("properties"),dict):
            raise ValueError("Malformed river observation")
        prop=feature["properties"]
        if prop.get("monitoring_location_id")!=SITE or str(prop.get("parameter_code"))!=PARAMETER or str(prop.get("statistic_id"))!=STATISTIC:
            raise ValueError("Unexpected site, parameter or statistic")
        stamp=prop.get("time")
        if not isinstance(stamp,str):raise ValueError("Invalid river local day")
        day=date.fromisoformat(stamp)
        if day.isoformat()!=stamp or not start<=stamp<=end:raise ValueError("USGS date outside requested window")
        series=prop.get("time_series_id",prop.get("timeseries_id"))
        identity=(stamp,str(series))
        if identity in seen:raise ValueError("Duplicate river observation")
        seen.add(identity)
        value=prop.get("value")
        if value is None:continue
        try:discharge=float(value)
        except (ValueError,TypeError) as exc:raise ValueError("Invalid river discharge") from exc
        if not math.isfinite(discharge) or discharge<0 or discharge>1e9:
            raise ValueError("USGS discharge outside plausible values")
        units=prop.get("unit_of_measure")
        if units not in ("ft3/s","ft^3/s","ft³/s","ft3 s-1"):
            raise ValueError("USGS discharge units unsupported: "+str(units))
        rows.append({"station":SITE,"date":stamp,"mean_discharge_cfs":discharge,
                    "parameter_code":PARAMETER,"statistic_id":STATISTIC,
                    "approval_status":str(prop.get("approval_status")or"Unknown")[:100],
                    "unit":"cfs"})
    if not rows:raise ValueError("No measured discharge observations in response")
    # Protect dashboard against multiple time series accidentally double-counting one day.
    if len({r["date"] for r in rows})!=len(rows):
        raise ValueError("Multiple discharge series on same day need explicit selection")
    return sorted(rows,key=lambda r:r["date"])

def fetch(start,end,folder=ROOT,opener=None):
    url=url_for(start,end);folder=Path(folder)
    stem=f"river-daily-01491000-{start}-to-{end}"
    snap=folder/(stem+".json");manifest=folder/(stem+".manifest.json")
    if snap.exists() or manifest.exists():raise FileExistsError("Existing river snapshot will not be replaced")
    req=urllib.request.Request(url,headers={"User-Agent":"DataNexus-AI-Enterprise/0.1","Accept":"application/geo+json,application/json"})
    with (opener or urllib.request.urlopen)(req,timeout=30) as resp:raw=resp.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError("USGS river response too large")
    rows=normalize(json.loads(raw),start,end)
    report={"source":"USGS modern daily-values API","site":SITE,"parameter":PARAMETER,
            "statistic":STATISTIC,"url":url,"start":start,"end":end,"count":len(rows),
            "retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
            "raw_sha256":hashlib.sha256(raw).hexdigest(),"records_sha256":digest(rows),
            "snapshot":snap.name,"continuous":False,"production_approved":False}
    folder.mkdir(parents=True,exist_ok=True)
    try:
        with snap.open("x",encoding="utf-8") as f:json.dump(rows,f,allow_nan=False)
        with manifest.open("x",encoding="utf-8") as f:json.dump(report,f,indent=2)
    except Exception:
        if snap.exists():snap.unlink()
        if manifest.exists():manifest.unlink()
        raise
    return {"status":"verified_local_snapshot","records":len(rows),"site":SITE,"manifest":str(manifest)}

def load(folder=ROOT):
    folder=Path(folder)
    manifests=sorted(folder.glob("river-daily-01491000-*.manifest.json"),reverse=True) if folder.is_dir() else []
    if not manifests:return None
    path=manifests[0]
    if path.is_symlink() or path.stat().st_size>12000:raise ValueError("Unsafe USGS river manifest")
    report=json.loads(path.read_text(encoding="utf-8"))
    keys={"source","site","parameter","statistic","url","start","end","count","retrieved_at_utc","raw_sha256","records_sha256","snapshot","continuous","production_approved"}
    if not isinstance(report,dict) or set(report)!=keys or report["source"]!="USGS modern daily-values API" or report["site"]!=SITE or report["parameter"]!=PARAMETER or report["statistic"]!=STATISTIC or report["continuous"] is not False or report["production_approved"] is not False:
        raise ValueError("Untrusted USGS river manifest")
    if report["url"]!=url_for(report["start"],report["end"]):raise ValueError("Unexpected USGS source URL")
    name=f"river-daily-01491000-{report['start']}-to-{report['end']}.json"
    if report["snapshot"]!=name:raise ValueError("Wrong river snapshot name")
    snapshot=folder/name
    if snapshot.is_symlink() or not snapshot.is_file() or snapshot.stat().st_size>2_000_000:raise ValueError("River snapshot missing")
    rows=json.loads(snapshot.read_text(encoding="utf-8"))
    if not isinstance(rows,list) or type(report["count"])is not int or len(rows)!=report["count"] or digest(rows)!=report["records_sha256"]:
        raise ValueError("USGS river snapshot integrity failure")
    expected={"station","date","mean_discharge_cfs","parameter_code","statistic_id","approval_status","unit"}
    if any(not isinstance(row,dict) or set(row)!=expected or row["station"]!=SITE or row["parameter_code"]!=PARAMETER or row["statistic_id"]!=STATISTIC or row["unit"]!="cfs" or type(row["mean_discharge_cfs"]) not in (float,int) or not math.isfinite(row["mean_discharge_cfs"]) or not 0<=row["mean_discharge_cfs"]<=1e9 or not report["start"]<=row["date"]<=report["end"] for row in rows):
        raise ValueError("Invalid stored river measurements")
    if len({r["date"] for r in rows})!=len(rows):raise ValueError("Duplicate stored river days")
    return {"metadata":report,"records":rows}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--start",default="2024-01-01")
    p.add_argument("--end",default="2024-01-07")
    p.add_argument("--execute",action="store_true")
    a=p.parse_args()
    if not a.execute:print(json.dumps({"mode":"plan","url":url_for(a.start,a.end),"writes":False},indent=2))
    else:print(json.dumps(fetch(a.start,a.end),indent=2))
