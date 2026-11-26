# Phase 3.2 — Bounded one-shot Kafka publication (MTA A/C/E)

**Prerequisite:** A local Redpanda cluster with topic `mta.subway.updates.v1` already created and described. The aviation topic remains untouched. A genuine MTA A/C/E feed response was separately verified during Phase 3.1.

This stage adds a one-shot publisher for **one aggregate event per validated GTFS-Realtime response**. It counts entities, trip updates, vehicle positions and alerts. It does **not** emit trip IDs, vehicle IDs, coordinates or raw transit protobuf. Publishing requires an explicit `--publish` switch; the default is a dry run (but still makes one official MTA API request). Freshness, schema, response provenance, topic existence and Kafka delivery confirmation are checked.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m pip install -e ".[kafka]"
python -m unittest discover -s tests -v
# First: one network request, no Kafka publication
python scripts/publish_mta_aggregate.py --feed ace
# Only after reviewing dry-run result: publish ONE aggregate record
python scripts/publish_mta_aggregate.py --feed ace --publish
docker compose exec redpanda rpk topic describe mta.subway.updates.v1 -X brokers=127.0.0.1:9092
```

The Kafka producer verifies one acknowledged delivery and returns partition/offset. That does not prove persistent consumer ingestion, deduplication across repeated runs, long-running operation or exactly-once semantics end-to-end. Producer idempotence protects retries in a single producer session only. Subsequent Phase 3.3: independent consumer, validation, durable checkpoints and safely scoped dashboard view.

There is no scheduler, streaming loop, production API, user-level authorization, or automated retries. Never publish to the aviation topic, enable public ports or use unapproved provider redistribution. **Production release remains BLOCKED (0/16).**
