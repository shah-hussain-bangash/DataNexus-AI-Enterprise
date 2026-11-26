# Phase 3.3 — MTA one-message consumer and durable local deduplication

The next step after one acknowledged `mta.subway.updates.v1` event (partition 0 offset 0) is a separate one-shot consumer. It validates the aggregate-only schema and Kafka key, writes the verified counts to a dedicated ignored SQLite database `data/dev/mta/mta_aggregate.sqlite3`, then manually commits the Kafka offset. The `event_id` primary key ensures restart-safe deduplication locally.

No aviation files are modified. No raw GTFS, trip identities or vehicle positions are persisted. The consumer makes no MTA API request; it reads a maximum of one queued Kafka record each time. It waits up to ten seconds by default, then returns `no_event_available` without a fabricated success report.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
docker compose ps
python scripts/consume_mta_aggregate.py --timeout 10
```

Expected first run when the topic contains the Phase 3.2 message: `state: stored`, `records_in_store: 1`, `offset_committed: true`. If the prior message was already consumed by this consumer group, `no_event_available` is possible. Do not reset offsets or delete Kafka volumes.

**Limitations:** The local SQLite insert and Kafka commit are separate transactions; a crash between them can replay the event, handled by the primary-key deduplication. This is not an enterprise multi-tenant deployment, a continuously running streaming pipeline, a live dashboard source or end-to-end exactly-once delivery. The topic retains default local development retention. Production release remains BLOCKED 0/16.
