# Phase 2B — Local Medallion Foundation

**Status:** Initial implementation. This is a reproducible local Bronze/Silver/Gold **JSONL reference export**, not yet Apache Spark, Flink, Iceberg, distributed stream processing, or cloud production.

## Rationale
The first verified implementation should prove data-contract and quality behavior before introducing distributed infrastructure. It reads the Phase 2A SQLite sink and produces deterministic, versionable snapshots. This step does not replace Kafka or claim real-time continuous lakehouse ingestion.

## Requirements
- Existing Windows PowerShell DataNexus checkout and Python installation.
- Kafka consumer has already stored the two fixture records, or use the Phase 2A runbook to populate SQLite.

## Run
```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python -m datanexus.lakehouse --db data/dev/aviation.sqlite3 --output data/lakehouse
Get-Content data/lakehouse/metrics.json
Get-Content data/lakehouse/gold/daily_aircraft_summary.jsonl
```

Expected with the two provided events (assuming no additional live records):
- bronze_records: 2
- silver_records: 2
- quarantined_records: 0
- gold_rows: 1
- daily gold event_count: 2 and distinct_aircraft: 2

Outputs:
- `data/lakehouse/bronze/aviation_events.jsonl`: raw normalized envelopes
- `data/lakehouse/silver/aviation_states.jsonl`: validated coordinate-bearing records
- `data/lakehouse/quarantine/invalid_records.jsonl`: rejected records with reason
- `data/lakehouse/gold/daily_aircraft_summary.jsonl`: per-tenant per-day aggregates
- `data/lakehouse/metrics.json`: run counts

All output files are written using atomic replacement on the local filesystem. Repeated exports replace the prior snapshot; they do not append duplicates. This is **not** an ACID lakehouse transaction across all output files.

## Validation evidence
Run tests (fixture tests do not require Docker or any API key) and record test output, Git commit SHA and metrics. Do not commit live data, keys, or proprietary records.

## Next design gate: distributed Phase 2C
1. Kafka consumer/stream processor with a durable checkpoint strategy.
2. Object storage such as MinIO/S3/ADLS.
3. Apache Iceberg or Delta tables in Bronze/Silver/Gold.
4. Spark Structured Streaming integration with deterministic integration tests.
5. Quarantine topic, schema evolution, data lineage and OpenTelemetry metrics.
6. Replay, load, restore and data-license checks.

The original OpenSky endpoint is polled; it is not a native continuous event feed.
