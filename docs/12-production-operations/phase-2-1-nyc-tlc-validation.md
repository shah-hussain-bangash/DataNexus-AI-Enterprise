# Phase 2.1 — NYC TLC genuine Parquet schema and row validation

**Purpose:** upgrade the existing checksummed raw Bronze download from unvalidated inventory to a **separate, reproducible local validation report**. The original file and manifest remain unchanged, the API continues to label the original Bronze inventory as unvalidated, and nothing is counted as Gold analytics, production streaming, source licensing approval, or release signoff.

## Existing prerequisite

Run the existing acquisition process only if the source file is absent:

```powershell
python scripts/ingest_nyc_tlc.py --year 2024 --month 1
```

The existing `data/dev/nyc_tlc/yellow_tripdata_2024-01.parquet` and its `.manifest.json` must both exist. Do not download or overwrite the existing source again if already present.

## Windows execution

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m pip install pyarrow
python -m unittest discover -s tests -v
python scripts/validate_nyc_tlc.py --file data/dev/nyc_tlc/yellow_tripdata_2024-01.parquet --output data/dev/nyc_tlc/validation
```

This reads the **real Parquet file** locally using PyArrow, verifies SHA-256 against acquisition metadata, checks required Yellow Taxi columns and their types, scans every row in bounded batches, reconciles footer row count, and counts null/negative/time-order/location anomalies. It does not retain any per-trip samples in the report.

The expected output is `data/dev/nyc_tlc/validation/yellow_tripdata_2024-01.parquet.validation.json`. That folder is local only. **Do not commit raw trip records or local outputs to GitHub**.

The validator refuses to overwrite existing validation reports; remove or archive an earlier report deliberately if rerunning after an update. If the Parquet schema differs from required fields the validation fails closed. Quality warnings do not silently alter or delete rows.

## Evidence interpretation

- `required_schema_validated=true` means checked against this initial local schema contract, **not** a production or regulator certification.
- `complete_row_scan=true` means every Parquet row passed through the local checks, not that all rows are valid.
- `quality_warning_counts` may contain overlapping per-row problems; do not sum warnings as an invalid-row count.
- `approved_snapshot=null`, `license_review=pending`, `published_reporting=false` and `enterprise_accepted=false` deliberately prohibit production claims.
- Next step after this validated run: approved Silver transformations, row-level quarantine and Gold aggregations, then authenticated tenant-scoped reporting APIs. Those features have **not been implemented** by this phase.

Production release: **BLOCKED (0/16)**.
