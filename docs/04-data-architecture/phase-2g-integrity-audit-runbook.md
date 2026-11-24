# Phase 2G — Read-only Iceberg integrity audit (first slice)

This first Phase 2G milestone checks the already verified Phase 2F REST catalog
and S3-compatible object store. It **does not modify** Iceberg tables, Spark
checkpoints or MinIO data. It fails on duplicate Silver `event_id`, null keys,
Gold-vs-Silver discrepancies, missing Iceberg snapshots, or an unexpected
Silver count. It also reports quarantine row count and catalog type.

This is a bounded, local **integrity audit**, not durability/restart proof,
HA/DR validation, continuous monitoring, incremental MERGE, or production
hardening. The REST fixture remains development-only.

## Windows PowerShell

Execute these commands separately from the DataNexus repository:

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
docker compose --env-file phase2f.env -f docker-compose.minio.yml -f docker-compose.audit.yml config --quiet
docker compose --env-file phase2f.env -f docker-compose.minio.yml ps
docker compose --env-file phase2f.env -f docker-compose.minio.yml -f docker-compose.audit.yml run --rm iceberg-audit
```

Expected marker: `DATANEXUS_ICEBERG_AUDIT=` ending in `"passed": true`,
with the existing test dataset: Silver 2, Gold 1, quarantine 0,
duplicate IDs 0, and Gold mismatches 0.

If the REST service is not running, start without resetting volumes:

```powershell
docker compose --env-file phase2f.env -f docker-compose.minio.yml up -d minio iceberg-rest
```

**Do not execute `docker compose down -v` or delete the warehouse bucket.**

## Why this is needed

The earlier Phase 2F job read back tables it had just written.
An independent read-only audit adds correctness checks and verifies that
Iceberg snapshot metadata remains queryable during an uninterrupted
catalog session.

## Remaining reliability gates

1. Establish a durable, backed-up REST catalog rather than a fixture.
2. Test a controlled catalog restart and verify table discovery afterward.
3. Add incremental `MERGE INTO` and replay/late-event tests.
4. Test deliberate malformed records, quarantine, recovery and audit evidence.
5. Add TLS, scoped credentials, retention, monitoring and operational SLOs.
