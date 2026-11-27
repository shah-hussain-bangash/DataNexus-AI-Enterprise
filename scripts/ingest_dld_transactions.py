"""DLD official Transactions CSV: strict, privacy-preserving local aggregate import.

No scraping, remote calls, invented records, or automatic permission grant.
Source URL and license status are recorded as operator-provided assertions.
Do not use for external publication before license and provenance review.
"""
import argparse,csv,hashlib,json,math,re
from collections import defaultdict
from datetime import datetime,timezone,date
from pathlib import Path

ROOT=Path("data/dev/dubai_property")
SOURCE="https://dubailand.gov.ae/en/open-data/real-estate-data/"
STEM="dld-transactions-local-review"
REQUIRED={"Transaction Number","Transaction Date","Transaction Type","Area","Property Type","Amount"}
EXCLUDED_FIELDS={"Transaction Number","No. of Buyer","No. of Seller"}
MAX_CSV_BYTES=60_000_000
MAX_ROWS=100_000
MAX_GROUPS=5000

def date_value(raw):
    raw=(raw or "").strip()
    for fmt in ("%Y-%m-%d","%d/%m/%Y","%d-%m-%Y","%m/%d/%Y"):
        try:
            d=datetime.strptime(raw,fmt).date()
            if date(2000,1,1)<=d<=datetime.now(timezone.utc).date():
                return d.isoformat()
        except ValueError:pass
    raise ValueError("Invalid DLD transaction date")

def currency(value):
    raw=(value or "").strip().replace(",","")
    try:n=float(raw)
    except (ValueError,TypeError) as e:raise ValueError("Invalid transaction amount") from e
    if not math.isfinite(n) or not 0<n<=100_000_000_000:raise ValueError("Out-of-range transaction amount")
    return round(n,2)

def summarize(stream):
    reader=csv.DictReader(stream)
    headers=set(reader.fieldnames or [])
    if not REQUIRED.issubset(headers) or any(not h or h.strip()!=h for h in headers):
        raise ValueError("Unsupported DLD CSV headers")
    if len(headers)!=len(reader.fieldnames):raise ValueError("Duplicate DLD column")
    buckets=defaultdict(lambda:[0,0.0])
    identifiers=set(); scanned=0; included=0; excluded=0
    for row in reader:
        scanned+=1
        if scanned>MAX_ROWS:raise ValueError("CSV exceeds maximum allowed transaction rows")
        if None in row or any(v is None for v in row.values()):raise ValueError("Malformed DLD CSV row")
        identity=(row["Transaction Number"] or "").strip()
        if not identity or len(identity)>128 or identity in identifiers:
            raise ValueError("Missing or duplicate transaction identifier")
        identifiers.add(identity)
        typ=(row["Transaction Type"] or "").strip().casefold()
        # Only sale transactions are prices. Never mix mortgage/gifts.
        if typ not in ("sale","sales"):
            excluded+=1
            continue
        day=date_value(row["Transaction Date"])
        area=(row["Area"] or "").strip()
        property_type=(row["Property Type"] or "").strip()
        if not area or not property_type or len(area)>120 or len(property_type)>100 or any(ord(c)<32 for c in area+property_type):
            raise ValueError("Invalid DLD area or property type")
        amount=currency(row["Amount"])
        key=(day,area,property_type)
        if key not in buckets and len(buckets)>=MAX_GROUPS:
            raise ValueError("More than maximum allowed aggregate groups")
        buckets[key][0]+=1;buckets[key][1]+=amount;included+=1
    if included==0:raise ValueError("No sale transactions in DLD CSV")
    records=[{"date":k[0],"area":k[1],"property_type":k[2],"sales_count":v[0],
        "total_amount_aed":round(v[1],2),"currency":"AED","source_kind":"DLD CSV operator supplied"}
        for k,v in sorted(buckets.items())]
    return records,{"source_rows":scanned,"sales_rows":included,"excluded_non_sales":excluded}

def checksum(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def digest(rows):
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def ingest(csv_path,folder=ROOT):
    csv_path=Path(csv_path);folder=Path(folder)
    if csv_path.suffix.lower()!=".csv" or csv_path.is_symlink() or not csv_path.is_file() or csv_path.stat().st_size>MAX_CSV_BYTES:
        raise ValueError("Select a local DLD CSV of no more than 60MB")
    snapshot=folder/(STEM+".json");manifest=folder/(STEM+".manifest.json")
    if snapshot.exists() or manifest.exists():raise FileExistsError("Existing DLD snapshot cannot be overwritten")
    source_hash=checksum(csv_path)
    with csv_path.open("r",encoding="utf-8-sig",newline="") as f: rows,counts=summarize(f)
    metadata={"source":"Dubai Land Department Transactions CSV","source_page":SOURCE,
        "operator_supplied":True,"source_provenance_verified":False,"license_approved":False,
        "contains_transaction_identifiers":False,"input_sha256":source_hash,
        "retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
        "count":len(rows),"records_sha256":digest(rows),"snapshot":snapshot.name,**counts,
        "continuous":False,"production_approved":False}
    folder.mkdir(parents=True,exist_ok=True)
    try:
        with snapshot.open("x",encoding="utf-8") as f:json.dump(rows,f,allow_nan=False)
        with manifest.open("x",encoding="utf-8") as f:json.dump(metadata,f,indent=2)
    except Exception:
        snapshot.unlink(missing_ok=True);manifest.unlink(missing_ok=True);raise
    return {"status":"local_csv_aggregated_provenance_review_required",**counts,"aggregate_groups":len(rows),"manifest":str(manifest)}

def load(folder=ROOT):
    folder=Path(folder)
    manifest=folder/(STEM+".manifest.json");snap=folder/(STEM+".json")
    if not manifest.exists():return None
    if manifest.is_symlink() or snap.is_symlink() or not snap.is_file() or manifest.stat().st_size>12000 or snap.stat().st_size>3_000_000:
        raise ValueError("Invalid DLD local snapshot")
    meta=json.loads(manifest.read_text(encoding="utf-8"))
    keys={"source","source_page","operator_supplied","source_provenance_verified","license_approved",
        "contains_transaction_identifiers","input_sha256","retrieved_at_utc","count","records_sha256",
        "snapshot","source_rows","sales_rows","excluded_non_sales","continuous","production_approved"}
    if not isinstance(meta,dict) or set(meta)!=keys or meta["source"]!="Dubai Land Department Transactions CSV" or meta["source_page"]!=SOURCE or meta["operator_supplied"] is not True or meta["source_provenance_verified"] is not False or meta["license_approved"] is not False or meta["contains_transaction_identifiers"] is not False or meta["continuous"] is not False or meta["production_approved"] is not False or meta["snapshot"]!=snap.name or not re.fullmatch("[0-9a-f]{64}",str(meta["input_sha256"])):
        raise ValueError("Untrusted DLD provenance metadata")
    rows=json.loads(snap.read_text(encoding="utf-8"))
    if not isinstance(rows,list) or type(meta["count"])is not int or len(rows)!=meta["count"] or digest(rows)!=meta["records_sha256"] or sum(x["sales_count"] for x in rows)!=meta["sales_rows"] or meta["source_rows"]!=meta["sales_rows"]+meta["excluded_non_sales"]:
        raise ValueError("DLD aggregate reconciliation failure")
    fields={"date","area","property_type","sales_count","total_amount_aed","currency","source_kind"}
    for x in rows:
        if not isinstance(x,dict) or set(x)!=fields or x["currency"]!="AED" or x["source_kind"]!="DLD CSV operator supplied" or date_value(x["date"])!=x["date"] or not x["area"] or not x["property_type"] or type(x["sales_count"])is not int or x["sales_count"]<=0 or type(x["total_amount_aed"])not in (float,int) or not math.isfinite(x["total_amount_aed"]) or x["total_amount_aed"]<=0:
            raise ValueError("Invalid DLD stored aggregate")
    return {"metadata":meta,"records":rows}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv",type=Path)
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    if not args.execute:
        print(json.dumps({"mode":"plan","source_page":SOURCE,"requires_manual_official_csv":True,
            "license_review":"pending","external_publication":False,"network_access":False,
            "writes":False},indent=2))
    else:
        if args.csv is None:p.error("--csv is required with --execute")
        print(json.dumps(ingest(args.csv),indent=2))
