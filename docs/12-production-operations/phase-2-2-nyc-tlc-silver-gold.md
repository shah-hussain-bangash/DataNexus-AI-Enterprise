# Phase 2.2 — Local NYC TLC Silver / quarantine / Gold artifacts

**Implemented:** isolated local PyArrow streaming-batch transformation with fail-closed Bronze/Phase-2.1 validation checks. No real dashboard data endpoint, live MTA connector, tenant data publication, Iceberg table or production signoff is created.

## Prerequisites

- Original NYC TLC January 2024 Yellow Taxi Parquet file and download manifest exist locally.
- Phase 2.1 report `data/dev/nyc_tlc/validation/yellow_tripdata_2024-01.parquet.validation.json` was successfully generated from the exact same source checksum.
- `python -m pip install pyarrow` in your active Python environment.

Check the validation evidence first:

```powershell
Get-Content "data/dev/nyc_tlc/validation/yellow_tripdata_2024-01.parquet.validation.json"
```

If it is missing, run Phase 2.1 from the repository instructions. Do not invent the dataset row count or mark an unvalidated file as approved.

## Run on Windows

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/transform_nyc_tlc.py --file data/dev/nyc_tlc/yellow_tripdata_2024-01.parquet --validation data/dev/nyc_tlc/validation/yellow_tripdata_2024-01.parquet.validation.json --output data/dev/nyc_tlc/silver_gold_2024_01
```

The command refuses to overwrite an existing output directory. Store all results under ignored `data/dev/`; never commit source Parquet, validation reports or data rows.

## Outputs

- `silver_trips.parquet`: bounded selected trip columns, only records meeting initial local quality rules
- `rejected_row_reasons.jsonl`: local row indices and rejection reasons, **not** raw trip payload
- `gold_daily_trips.parquet`: aggregated pickup-date count, distance and fare totals
- `transform_manifest.json`: source SHA-256, reconciliation, acceptance limitations and provenance

Mandatory invariants: `source_rows = silver_rows + quarantined_rows`; `sum(gold.trip_count) = silver_rows`. Quality rules are preliminary: exclude negative totals (including possible refunds), negative distance, invalid timestamps and location IDs. Quality policy and licensing need independent review before business use.

This is local development-only Parquet and **not** a governed production lakehouse. Approved source licensing, multi-tenant controls, reproducibility evidence, and production operation are absent. Production release: **BLOCKED 0/16**.
