# Phase 2C — Spark batch foundation (first slice)

**Current scope:** Apache Spark local[2] DataFrame job in Docker, reading the Phase 2B validated Silver JSONL and writing Parquet Silver, quarantine, and Gold. It is not yet Spark Structured Streaming, distributed across machines, a Kafka direct stream, MinIO/S3, Apache Iceberg, or a production lakehouse.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python -m datanexus.lakehouse --db data/dev/aviation.sqlite3 --output data/lakehouse
docker compose -f docker-compose.spark.yml config --quiet
docker compose -f docker-compose.spark.yml run --rm spark
```

The first Spark image download can take significant time. Docker Desktop must be running. The command expects exactly two valid Silver aviation fixture events; if your database also contains other data, edit/remove the optional `--expected-events 2` arguments in `docker-compose.spark.yml` and review resulting metrics.

Expected terminal marker:
```text
DATANEXUS_SPARK_METRICS={"gold_rows": 1, "quarantined_records": 0, "silver_records": 2, "storage_format": "parquet_spark_batch"}
```

Output directories (not single files, because Spark writes partitioned Parquet file sets):
- `data/spark/silver_parquet`
- `data/spark/quarantine_parquet`
- `data/spark/gold_parquet`

Inspect output filenames:
```powershell
Get-ChildItem data/spark/gold_parquet
```

**Data handling:** Spark overwrites each output path separately. A failed run can leave mismatched snapshots. Do not use for production workloads, regulated data or multi-tenant isolation.

## Next acceptance gates

1. Verify Docker Spark job succeeds on Windows using the two-row fixture.
2. Add Kafka Structured Streaming with checkpoint and replay tests.
3. Add MinIO/S3-compatible object storage and Iceberg/Delta commit semantics.
4. Add larger deterministic fixtures, schema-evolution cases, data-quality quarantine and performance tests.
5. Add dashboards and observable SLIs with failure recovery evidence.

The Phase 2B source files remain unchanged by the Spark job.
