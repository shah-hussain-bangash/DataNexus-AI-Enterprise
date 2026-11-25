"""Bounded public NYC TLC parquet acquisition (Bronze raw only; NOT analytics).

Usage: python scripts/ingest_nyc_tlc.py --year 2024 --month 1
Never loads arbitrary URLs and never treats a downloaded parquet as validated Gold.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES=180*1024*1024
BASE="https://d37ci6vzurychx.cloudfront.net/trip-data/"
SOURCE_PAGE="https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"

def source_url(year, month):
    if not isinstance(year,int) or year<2009 or year>datetime.now(timezone.utc).year:
        raise ValueError("year outside published NYC TLC range")
    if not isinstance(month,int) or month<1 or month>12:
        raise ValueError("month must be 1..12")
    if (year,month) > (datetime.now(timezone.utc).year,datetime.now(timezone.utc).month):
        raise ValueError("future month cannot have published data")
    name=f"yellow_tripdata_{year:04d}-{month:02d}.parquet"
    return BASE+name,name

def validate_parquet_header(path):
    """Basic file signature validation, not semantic/schema/row-count validation."""
    with open(path,"rb") as stream:
        if stream.read(4)!=b"PAR1":
            raise ValueError("download missing Parquet header")
        stream.seek(0,os.SEEK_END)
        size=stream.tell()
        if size<12:raise ValueError("parquet download too small")
        stream.seek(-4,os.SEEK_END)
        if stream.read(4)!=b"PAR1":raise ValueError("download missing Parquet footer")
    return size

def download_month(year,month,root,opener=urllib.request.urlopen):
    url,name=source_url(year,month)
    target_dir=Path(root).resolve()/"nyc_tlc"
    target_dir.mkdir(parents=True,exist_ok=True)
    target=target_dir/name
    manifest=target_dir/(name+".manifest.json")
    if target.exists() or manifest.exists():
        raise FileExistsError("Dataset or manifest exists; no silent overwrite")
    fd,tmp=tempfile.mkstemp(prefix=".partial-tlc-",dir=target_dir)
    sha=hashlib.sha256()
    total=0
    try:
        with os.fdopen(fd,"wb") as out:
            req=urllib.request.Request(url,headers={"User-Agent":"DataNexusLocalResearch/0.1"})
            with opener(req,timeout=45) as response:
                final=response.geturl() if hasattr(response,"geturl") else url
                if final!=url:
                    raise ValueError("unexpected remote redirect")
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    total+=len(chunk)
                    if total>MAX_BYTES:raise ValueError("download exceeds local acquisition limit")
                    out.write(chunk)
                    sha.update(chunk)
            out.flush()
            os.fsync(out.fileno())
        size=validate_parquet_header(tmp)
        metadata={
            "source":"nyc_tlc_yellow_taxi",
            "publisher":"NYC Taxi and Limousine Commission",
            "publisher_documentation":SOURCE_PAGE,
            "source_url":url,
            "file_name":name,
            "period":f"{year:04d}-{month:02d}",
            "sha256":sha.hexdigest(),
            "bytes":size,
            "downloaded_at_utc":datetime.now(timezone.utc).isoformat(),
            "stage":"bronze_downloaded_unvalidated",
            "schema_validated":False,
            "row_count":None,
            "license_review":"pending",
            "approved_snapshot":None,
        }
        os.replace(tmp,target)
        # Write manifest last, so the API doesn't report partial data.
        fd2,meta_tmp=tempfile.mkstemp(prefix=".partial-manifest-",dir=target_dir)
        try:
            with os.fdopen(fd2,"w",encoding="utf-8") as stream:
                json.dump(metadata,stream,sort_keys=True,indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(meta_tmp,manifest)
        finally:
            if os.path.exists(meta_tmp):os.unlink(meta_tmp)
        return metadata
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year",type=int,default=2024)
    parser.add_argument("--month",type=int,default=1)
    parser.add_argument("--data-root",default="data/dev")
    args=parser.parse_args()
    result=download_month(args.year,args.month,args.data_root)
    print(json.dumps(result,indent=2))
    print("Downloaded raw Bronze only. NO analytics/row counts or publishing was performed.")

if __name__=="__main__":
    try:main()
    except (ValueError,FileExistsError,urllib.error.URLError,OSError) as exc:
        print("NYC TLC acquisition failed:",exc,file=sys.stderr)
        sys.exit(1)
