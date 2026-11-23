# Phase 2D — Kafka to Spark Structured Streaming Bronze (bounded streaming)

**Status:** Initial code committed; Docker integration must be tested on Windows.

This phase adds **Spark Structured Streaming** against the existing Redpanda
Kafka topic and writes **append-only Bronze Parquet** with a durable
filesystem checkpoint. Its `availableNow` trigger consumes currently available
offsets and then exits. This is real Spark streaming execution in a bounded
mode, not a continuous always-on service or a production-grade lakehouse.

## Windows PowerShell

Run each command separately in the already verified repository:

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
docker compose up -d redpanda
docker compose exec redpanda rpk topic list
python -m datanexus.cli collect --mode fixture --bootstrap 127.0.0.1:19092
docker compose -f docker-compose.yml -f docker-compose.streaming.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.streaming.yml run --rm spark-stream
Get-ChildItem data/streaming/bronze_parquet
Get-ChildItem data/streaming/checkpoints/aviation_bronze_v1
```

Expected markers: `DATANEXUS_STREAM_COMPLETED=`, a Parquet part file and
`_spark_metadata` under `data/streaming/bronze_parquet`, plus offset/commit
metadata in the checkpoint. The record count is **not** expected to equal 2:
the Kafka topic may contain previously republished fixture events. Bronze
intentionally retains repeats, with event_id and Kafka offsets for lineage.

Restart the same streaming command without republishing fixture records.
With an unchanged checkpoint there should be no new Kafka offsets to ingest,
and no duplicate Bronze rows appended. To test new offsets, republish fixtures
and restart the job. Do not delete the checkpoint when resuming; changing
checkpoint paths or resetting Redpanda may replay data.

## Notes and limitations

- The Spark Kafka connector is pulled with `--packages` from Maven; first
  execution requires network access to the Maven repository. Failures such as
  unresolved dependencies can result from proxy, DNS or remote availability.
- The Spark job shares the existing Redpanda network using the two Compose
  files, so it connects to `redpanda:9092` rather than Windows localhost.
- Kafka is at-least-once and this Bronze layer retains duplicates intentionally;
  event_id-based deduplication is a planned Silver step.
- Basic parsed-field `quality_reason` labels are informational in Bronze.
  Malformed records are retained, not silently discarded.
- No integrated streaming Gold view, object storage, Iceberg transactions,
  multi-node cluster, security isolation, or operational SLOs have been verified.
- The existing Phase 2C batch Spark job remains unchanged.

## Next gate

1. Verify Docker job + checkpoint behavior on Windows.
2. Build Silver validation and idempotent event_id deduplication.
3. Add replay test and quarantine routing.
4. Introduce Iceberg plus S3-compatible storage and recovery tests.
