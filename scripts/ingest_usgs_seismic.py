"""Bounded opt-in USGS historical GeoJSON acquisition; no simulated data."""
import argparse,hashlib,json,math,urllib.parse,urllib.request
from datetime import date,datetime,timezone
from pathlib import Path
URL="https://earthquake.usgs.gov/fdsnws/event/1/query"
OUT=Path("data/dev/usgs_seismic")
def query(start,end,mag=4.5):
 a,b=date.fromisoformat(start),date.fromisoformat(end)
 if not a<b or (b-a).days>31 or b>datetime.now(timezone.utc).date():raise ValueError("Invalid completed historical window")
 if not 0<=mag<=9:raise ValueError("Invalid minimum magnitude")
 return URL+"?"+urllib.parse.urlencode({"format":"geojson","starttime":start,"endtime":end,"minmagnitude":mag,"orderby":"time-asc","limit":5000})
def normalize(payload,start,end):
 if payload.get("type")!="FeatureCollection" or not isinstance(payload.get("features"),list):raise ValueError("Invalid GeoJSON")
 rows=payload["features"]
 if not isinstance(payload.get("metadata"),dict):raise ValueError("Missing USGS metadata")
 count=payload["metadata"].get("count")
 # USGS GeoJSON metadata.count is optional; never require it to be present.
 # When supplied, it must be a nonnegative integer and match features.
 if count is not None and (type(count) is not int or count!=len(rows)):
  raise ValueError(f"USGS count mismatch: metadata_count={count!r}, returned_features={len(rows)}")
 if not rows:raise ValueError("USGS returned zero events; try another historical window or smaller minimum magnitude")
 if len(rows)>=5000:raise ValueError(f"USGS result reached query limit: {len(rows)}; split into smaller historical windows")
 begin=int(datetime.fromisoformat(start+"T00:00:00+00:00").timestamp()*1000)
 finish=int(datetime.fromisoformat(end+"T00:00:00+00:00").timestamp()*1000)
 events=[];seen=set()
 for f in rows:
  props=f.get("properties");geom=f.get("geometry")
  if not isinstance(f,dict) or f.get("type")!="Feature" or not isinstance(f.get("id"),str) or not 1<=len(f["id"])<=100 or f["id"] in seen or not isinstance(props,dict) or not isinstance(geom,dict) or geom.get("type")!="Point":raise ValueError("Invalid event structure")
  seen.add(f["id"]);xyz=geom.get("coordinates")
  if not isinstance(xyz,list) or len(xyz)<3:raise ValueError("Invalid point")
  lon,lat,depth=xyz[:3];mag=props.get("mag");ms=props.get("time")
  if any(type(x) not in (float,int) or not math.isfinite(x) for x in (lon,lat,depth,mag)) or type(ms)is not int:raise ValueError("Invalid numeric data")
  if not(-180<=lon<=180 and -90<=lat<=90 and -100<=depth<=1000 and -2<=mag<=10 and begin<=ms<finish):raise ValueError("Out-of-range event")
  moment=datetime.fromtimestamp(ms/1000,timezone.utc)
  events.append({"event_id":f["id"],"date":moment.date().isoformat(),"event_utc":moment.isoformat(),"magnitude":mag,"latitude":lat,"longitude":lon,"depth_km":depth,"place":str(props.get("place")or"Unknown")[:200]})
 return events
def fetch(start,end,mag=4.5,folder=OUT,opener=None):
 url=query(start,end,mag);folder=Path(folder)
 stem="usgs-"+start+"-to-"+end+"-m"+str(mag)
 snapshot=folder/(stem+".json");manifest=folder/(stem+".manifest.json")
 if snapshot.exists() or manifest.exists():raise FileExistsError("Snapshot exists; no overwrite")
 req=urllib.request.Request(url,headers={"User-Agent":"DataNexus-Education/1.0","Accept":"application/json"})
 with (opener or urllib.request.urlopen)(req,timeout=20) as resp:
  raw=resp.read(8_000_001)
 if len(raw)>8_000_000:raise ValueError("Response too large")
 events=normalize(json.loads(raw),start,end)
 report={"source":"USGS ComCat","url":url,"start":start,"end":end,"count":len(events),
  "retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
  "raw_sha256":hashlib.sha256(raw).hexdigest(),
  "records_sha256":hashlib.sha256(json.dumps(events,sort_keys=True).encode()).hexdigest(),
  "snapshot":snapshot.name,"production_approved":False,"continuous":False}
 folder.mkdir(parents=True,exist_ok=True)
 try:
  with snapshot.open("x",encoding="utf-8") as f:json.dump(events,f)
  with manifest.open("x",encoding="utf-8") as f:json.dump(report,f,indent=2)
 except Exception:
  if snapshot.exists():snapshot.unlink()
  if manifest.exists():manifest.unlink()
  raise
 return {"status":"verified_local_snapshot","records":len(events),"manifest":str(manifest)}
def load(folder=OUT):
 folder=Path(folder);files=sorted(folder.glob("usgs-*.manifest.json"),reverse=True) if folder.exists() else []
 if not files:return None
 p=files[0]
 if p.is_symlink() or p.stat().st_size>10000:raise ValueError("Unsafe manifest")
 report=json.loads(p.read_text(encoding="utf-8"))
 if report.get("source")!="USGS ComCat" or report.get("production_approved") is not False or report.get("continuous") is not False:raise ValueError("Unverified report")
 name=report["snapshot"]
 if not isinstance(name,str) or not name.startswith("usgs-") or not name.endswith(".json") or "/" in name or "\\" in name:raise ValueError("Invalid snapshot path")
 snap=folder/name
 if snap.is_symlink() or not snap.is_file() or snap.stat().st_size>8_000_000:raise ValueError("Snapshot missing")
 events=json.loads(snap.read_text(encoding="utf-8"))
 if len(events)!=report["count"] or hashlib.sha256(json.dumps(events,sort_keys=True).encode()).hexdigest()!=report["records_sha256"]:raise ValueError("Changed records")
 for row in events:
  if set(row)!={"event_id","date","event_utc","magnitude","latitude","longitude","depth_km","place"} or not report["start"]<=row["date"]<report["end"]:raise ValueError("Invalid record")
 return {"metadata":report,"records":events}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--start",default="2024-01-01")
 p.add_argument("--end",default="2024-01-08")
 p.add_argument("--min-magnitude",type=float,default=4.5)
 p.add_argument("--execute",action="store_true")
 a=p.parse_args()
 if not a.execute:print(json.dumps({"mode":"plan","url":query(a.start,a.end,a.min_magnitude),"writes":False},indent=2))
 else:print(json.dumps(fetch(a.start,a.end,a.min_magnitude),indent=2))
