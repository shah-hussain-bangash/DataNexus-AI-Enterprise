"""Read local NYC TLC raw manifests defensively; metadata only, never raw records."""
import json
import re
from pathlib import Path

FILE_PATTERN=re.compile(r"^yellow_tripdata_(20[0-9]{2})-(0[1-9]|1[0-2])\\.parquet\\.manifest\\.json$")

def available_downloads(root):
    directory=Path(root).resolve()/"nyc_tlc"
    if not directory.is_dir():return []
    records=[]
    for path in sorted(directory.glob("*.manifest.json"))[:36]:
        if not FILE_PATTERN.fullmatch(path.name) or path.is_symlink():continue
        if path.stat().st_size>16384:continue
        try:
            record=json.loads(path.read_text(encoding="utf-8"))
            parquet=directory/path.name.removesuffix(".manifest.json")
            if not parquet.is_file() or parquet.is_symlink():continue
            if record.get("stage")!="bronze_downloaded_unvalidated":continue
            if record.get("file_name")!=parquet.name:continue
            if not re.fullmatch(r"[0-9a-f]{64}",str(record.get("sha256",""))):continue
            if record.get("bytes")!=parquet.stat().st_size:continue
            if record.get("schema_validated") is not False:continue
            records.append({
                "period":record.get("period"),
                "file_name":record.get("file_name"),
                "bytes":record.get("bytes"),
                "sha256":record.get("sha256"),
                "stage":"bronze_downloaded_unvalidated",
                "schema_validated":False,
                "row_count":None,
                "approved_snapshot":None,
                "source":"nyc_tlc_yellow_taxi",
            })
        except (ValueError,TypeError,OSError,KeyError):
            continue
    return records
