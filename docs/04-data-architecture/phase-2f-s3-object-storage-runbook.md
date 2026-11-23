# Phase 2F — MinIO and Iceberg REST catalog proof of concept

## Scope
A **separate** Docker Compose project adds:
- A persistent MinIO bucket `warehouse` (S3-compatible) on a named Docker volume
- A one-time MinIO client bucket initialization
- An **Apache Iceberg REST fixture catalog** (development-only, NOT a production catalog)
- An Apache Spark batch job that uses the shared Phase 2D Bronze Parquet
  and writes **Silver, quarantine, Gold Iceberg tables to MinIO**.

This is *not* a production S3 system. The REST fixture's metadata persistence
and restart durability have not been established; an S3 bucket alone does not
guarantee usable tables without their catalog records. Do not use live sensitive
data. This configuration does not change Phase 2E's local catalog.

This follows the general Spark / REST catalog / S3FileIO approach in the
Apache Iceberg quickstart: https://iceberg.apache.org/spark-quickstart/

## Windows PowerShell steps (run separately)

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
Test-Path data/streaming/bronze_parquet/_spark_metadata
Copy-Item phase2f.env.template phase2f.env
notepad phase2f.env
```

**Change the demo secret** in Notepad and save. Do not share credentials in a chat
or GitHub. The Compose service ports bind to 127.0.0.1 only.

```powershell
docker compose --env-file phase2f.env -f docker-compose.minio.yml config --quiet
docker compose --env-file phase2f.env -f docker-compose.minio.yml up -d minio iceberg-rest
docker compose --env-file phase2f.env -f docker-compose.minio.yml ps
docker compose --env-file phase2f.env -f docker-compose.minio.yml run --rm iceberg-s3
```

Expected: `DATANEXUS_S3_ICEBERG_METRICS=` with Bronze 12,
unique Silver 2, quarantined 0, Gold 1 for the historical fixture.
If REST startup is still in progress, first inspect
`docker compose --env-file phase2f.env -f docker-compose.minio.yml logs --tail 80 iceberg-rest` and retry.

View local MinIO console at http://127.0.0.1:19001 and verify
the `warehouse` bucket has `datanexus` table objects.

## Safety and recovery limitations

- Never use `docker compose down -v`; that deletes the object-store volume.
- Use `docker compose ... stop` to stop services without removing volumes.
- `phase2f.env` is ignored by Git; do not commit it.
- The object store has no TLS or access policies beyond development credentials;
  only localhost host ports are published.
- The REST catalog image is a **fixture for development**, not a supported HA
  metadata service. For a reliable restart / persistence gate, migrate to
  a durable JDBC-backed REST catalog (or Polaris / Nessie) and back it up.
- Spark rebuilds Silver/Gold from all Bronze on each run, so it is not yet
  incrementally maintained. Table replacement may create orphaned files
  over repeated runs and needs snapshot expiration and cleanup.
- Table transactions are per table, not across all three tables.
- Re-running without changing Bronze should yield the same unique Silver and
  Gold counts; that is a data count verification, not an HA/DR test.

## Next gates
- Document and verify catalog metadata durability on container restart.
- Build incremental MERGE-based writes with operational replay tests.
- Add policy, IAM-like credentials separation, TLS, monitoring, retention,
  compaction, backup/restore and continuous streaming integration.
