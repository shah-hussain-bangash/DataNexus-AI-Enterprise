"""Bounded EIA v2 hourly US48 demand historical acquisition for Power BI.

EIA_API_KEY environment variable required only for --execute. Never record
or print API credentials, complete authenticated URLs, or provider raw data.
"""
import argparse,hashlib,json,math,os,socket,ssl,urllib.parse,urllib.request,urllib.error
from datetime import datetime,timezone,date
from pathlib import Path

ENDPOINT="https://api.eia.gov/v2/electricity/rto/region-data/data/"
ROOT=Path("data/dev/eia_energy")
RESPONDENT="US48"
SERIES="D"
LIMIT=1000

def query_params(start,end):
    a=date.fromisoformat(start);b=date.fromisoformat(end)
    if not a<=b or (b-a).days>7 or b>=datetime.now(timezone.utc).date():
        raise ValueError("Require a completed historical window of 8 days or less")
    return {"frequency":"hourly","data[0]":"value",
            "facets[respondent][]":RESPONDENT,"facets[type][]":SERIES,
            "start":start+"T00","end":end+"T23","sort[0][column]":"period",
            "sort[0][direction]":"asc","offset":0,"length":LIMIT}

def public_url(start,end):
    return ENDPOINT+"?"+urllib.parse.urlencode(query_params(start,end))

def digest(records):
    return hashlib.sha256(json.dumps(records,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def normalize(payload,start,end):
    if not isinstance(payload,dict) or not isinstance(payload.get("response"),dict):
        raise ValueError("Invalid EIA API response")
    response=payload["response"]
    rows=response.get("data")
    if not isinstance(rows,list) or not 0<len(rows)<LIMIT:
        raise ValueError("Empty or limit-sized EIA result; use a smaller date range")
    total=response.get("total")
    if total is None or not str(total).isdigit() or int(total)!=len(rows):
        raise ValueError(f"EIA data incomplete: reported total={total!r}, returned rows={len(rows)}")
    seen=set();out=[]
    for row in rows:
        if not isinstance(row,dict) or row.get("respondent")!=RESPONDENT or row.get("type")!=SERIES:
            raise ValueError("Unexpected EIA respondent or series type")
        stamp=row.get("period")
        if not isinstance(stamp,str):raise ValueError("Invalid EIA period")
        try:dt=datetime.strptime(stamp,"%Y-%m-%dT%H")
        except ValueError as exc:raise ValueError("Unsupported EIA UTC hourly period") from exc
        if dt.strftime("%Y-%m-%dT%H")!=stamp or not start<=dt.date().isoformat()<=end or stamp in seen:
            raise ValueError("EIA time out of range or duplicate")
        seen.add(stamp)
        if row.get("value") is None:raise ValueError("Missing EIA demand")
        try:value=float(row["value"])
        except (TypeError,ValueError) as exc:raise ValueError("Invalid EIA demand") from exc
        if not math.isfinite(value) or not 0<=value<=2_000_000:
            raise ValueError("EIA megawatt measurement out of bounds")
        if row.get("value-units")!="megawatthours":
            raise ValueError("Unsupported EIA source units: "+str(row.get("value-units")))
        out.append({"respondent":RESPONDENT,"date":dt.date().isoformat(),
            "period_utc":stamp,"demand_mwh":value,"source_unit":"megawatthours",
            "series_type":SERIES})
    return sorted(out,key=lambda r:r["period_utc"])

def safe_eia_http_error(exc):
    """Only report HTTP status and EIA's alphanumeric error code; never URL/body."""
    status=getattr(exc,"code",None)
    try:
        body=exc.read(4096)
        data=json.loads(body)
        error=data.get("error") if isinstance(data,dict) else None
        code=error.get("code") if isinstance(error,dict) else data.get("code") if isinstance(data,dict) else None
    except Exception:
        code=None
    if not isinstance(code,str) or len(code)>80 or not all(c.isascii() and (c.isalnum() or c=="_") for c in code):
        code="UNAVAILABLE"
    if type(status) is not int or not 100<=status<=599:status="UNKNOWN"
    return f"EIA request rejected (HTTP {status}; provider_code={code}; credential and URL hidden)"

def safe_network_reason(exc):
    """Classify network failures using exception classes, not messages/URLs."""
    root=exc
    if isinstance(exc,urllib.error.URLError):
        root=getattr(exc,"reason",None)
    if isinstance(root,ssl.SSLCertVerificationError):
        return "TLS_CERTIFICATE_VERIFICATION"
    if isinstance(root,ssl.SSLError):
        return "TLS_HANDSHAKE"
    if isinstance(root,socket.gaierror):
        return "DNS_RESOLUTION"
    if isinstance(root,(TimeoutError,socket.timeout)):
        return "TIMEOUT"
    if isinstance(root,ConnectionRefusedError):
        return "CONNECTION_REFUSED"
    if isinstance(root,ConnectionResetError):
        return "CONNECTION_RESET"
    if isinstance(root,PermissionError):
        return "LOCAL_NETWORK_PERMISSION"
    return "NETWORK_UNCLASSIFIED"

def fetch(start,end,folder=ROOT,opener=None,key=None):
    parameters=query_params(start,end)
    credential=key if key is not None else os.getenv("EIA_API_KEY")
    if not isinstance(credential,str) or not credential.strip() or len(credential)>256:
        raise ValueError("Set EIA_API_KEY in your local environment before executing")
    folder=Path(folder)
    stem=f"eia-us48-hourly-demand-{start}-to-{end}"
    snapshot=folder/(stem+".json");manifest=folder/(stem+".manifest.json")
    if snapshot.exists() or manifest.exists():raise FileExistsError("Existing EIA snapshot cannot be overwritten")
    authenticated=ENDPOINT+"?"+urllib.parse.urlencode({**parameters,"api_key":credential})
    request=urllib.request.Request(authenticated,headers={"Accept":"application/json","User-Agent":"DataNexus-AI-Enterprise/0.1"})
    try:
        with (opener or urllib.request.urlopen)(request,timeout=30) as response:
            raw=response.read(3_000_001)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(safe_eia_http_error(exc)) from None
    except Exception as exc:
        # Do not stringify exc: urllib errors may include authenticated URLs.
        reason=safe_network_reason(exc)
        raise RuntimeError(f"EIA request failed ({reason}; URL and credential hidden)") from None
    if len(raw)>3_000_000:raise ValueError("Oversized EIA response")
    rows=normalize(json.loads(raw),start,end)
    meta={"source":"EIA hourly electric grid demand","respondent":RESPONDENT,
        "series":SERIES,"public_query":public_url(start,end),"start":start,"end":end,
        "count":len(rows),"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
        "raw_sha256":hashlib.sha256(raw).hexdigest(),"records_sha256":digest(rows),
        "snapshot":snapshot.name,"continuous":False,"production_approved":False}
    folder.mkdir(parents=True,exist_ok=True)
    try:
        with snapshot.open("x",encoding="utf-8") as f:json.dump(rows,f,allow_nan=False)
        with manifest.open("x",encoding="utf-8") as f:json.dump(meta,f,indent=2)
    except Exception:
        if snapshot.exists():snapshot.unlink()
        if manifest.exists():manifest.unlink()
        raise
    return {"state":"verified_local_snapshot","rows":len(rows),"respondent":RESPONDENT,"manifest":str(manifest)}

def load(folder=ROOT):
    folder=Path(folder)
    files=sorted(folder.glob("eia-us48-hourly-demand-*.manifest.json"),reverse=True) if folder.is_dir() else []
    if not files:return None
    path=files[0]
    if path.is_symlink() or path.stat().st_size>12000:raise ValueError("Unsafe EIA manifest")
    meta=json.loads(path.read_text(encoding="utf-8"))
    keys={"source","respondent","series","public_query","start","end",
          "count","retrieved_at_utc","raw_sha256","records_sha256","snapshot",
          "continuous","production_approved"}
    if not isinstance(meta,dict) or set(meta)!=keys or meta["source"]!="EIA hourly electric grid demand" or meta["respondent"]!=RESPONDENT or meta["series"]!=SERIES or meta["continuous"] is not False or meta["production_approved"] is not False:
        raise ValueError("Untrusted EIA manifest")
    if meta["public_query"]!=public_url(meta["start"],meta["end"]):
        raise ValueError("EIA query does not match approved region and dates")
    expected=f"eia-us48-hourly-demand-{meta['start']}-to-{meta['end']}.json"
    if meta["snapshot"]!=expected:raise ValueError("EIA snapshot identifier invalid")
    snapshot=folder/expected
    if snapshot.is_symlink() or not snapshot.is_file() or snapshot.stat().st_size>3_000_000:
        raise ValueError("EIA snapshot missing")
    rows=json.loads(snapshot.read_text(encoding="utf-8"))
    if not isinstance(rows,list) or type(meta["count"])is not int or len(rows)!=meta["count"] or digest(rows)!=meta["records_sha256"]:
        raise ValueError("EIA snapshot hash or record count mismatch")
    fields={"respondent","date","period_utc","demand_mwh","source_unit","series_type"}
    if any(not isinstance(row,dict) or set(row)!=fields or row["respondent"]!=RESPONDENT or row["series_type"]!=SERIES or row["source_unit"]!="megawatthours" or not meta["start"]<=row["date"]<=meta["end"] or type(row["demand_mwh"])not in (int,float) or not math.isfinite(row["demand_mwh"]) or not 0<=row["demand_mwh"]<=2_000_000 for row in rows):
        raise ValueError("EIA stored observations failed validation")
    if len({row["period_utc"] for row in rows})!=len(rows):
        raise ValueError("Duplicate EIA stored periods")
    return {"metadata":meta,"records":rows}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start",default="2024-01-01")
    p.add_argument("--end",default="2024-01-07")
    p.add_argument("--execute",action="store_true")
    a=p.parse_args()
    if not a.execute:print(json.dumps({"mode":"plan","public_query":public_url(a.start,a.end),"credential_included":False,"writes":False},indent=2))
    else:print(json.dumps(fetch(a.start,a.end),indent=2))
