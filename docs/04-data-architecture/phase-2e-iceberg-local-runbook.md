# Phase 2E — Iceberg local transactional tables

## Scope

This is an **initial Iceberg local-catalog milestone** rather than the final
enterprise object-store implementation. It runs Spark 3.5.5 with Iceberg 1.9.2
in Docker against the existing Phase 2D Bronze Parquet. The local Hadoop catalog
stores Iceberg metadata and files on a Docker-mounted Windows directory.

Each table refresh commits a new Iceberg snapshot. The pipeline performs
bounded batch refreshes, **not** incremental Spark streaming writes, and the
three table updates are not mutually atomic.

It intentionally deduplicates repeated fixture events by stable `event_id`
in Silver. Bronze keeps all Kafka offset copies.

## Windows commands — execute separately

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
Test-Path data/streaming/bronze_parquet/_spark_metadata
docker compose -f docker-compose.iceberg.yml config --quiet
docker compose -f docker-compose.iceberg.yml run --rm iceberg-local
Get-ChildItem data/iceberg/warehouse/datanexus
```

Expected marker: `DATANEXUS_ICEBERG_METRICS=`.
With the confirmed 12 duplicated fixture messages in Bronze, expected:
`bronze_records=12`, `silver_unique_records=2`,
`quarantined_records=0`, `gold_rows=1`.

The expected unique number is deliberately hard-coded for the known fixture
test. If running other data, change the `--expected-unique` value or remove
that argument to accept all unique events.

Run the Iceberg Docker job a second time to test reproducible output.
Do not delete `data/streaming` or `data/iceberg`: the former holds a verified
checkpointed stream and the latter holds persistent Iceberg table metadata.

## Current limitations / next gates

- Local Hadoop catalog: not remote S3/MinIO.
- Bounded replay and table-snapshot refresh: not a continuous Iceberg sink.
- Silver quarantines rows with Bronze quality reasons, missing or invalid event
  timestamps, and missing or out-of-range coordinates. It also checks coordinates
  when reprocessing Bronze written by earlier versions.
- Rows with a non-null `reason` go into a quarantine table; missing or invalid
  dates currently cause rows to be excluded, not quarantined. Improve coverage.
- There is no security authorization, catalog HA, multi-table atomicity, compaction,
  schema evolution recovery, cost monitoring, or disaster recovery.
- Next: MinIO S3-compatible bucket and a managed/REST Iceberg catalog,
  incremental write strategy with idempotent MERGE, and recovery tests.

## Existing verified stages

- Phase 2A Kafka source → SQLite sink
- Phase 2B JSONL reference medallion
- Phase 2C Spark Parquet batch
- Phase 2D Kafka → checkpointed Spark Bronze
