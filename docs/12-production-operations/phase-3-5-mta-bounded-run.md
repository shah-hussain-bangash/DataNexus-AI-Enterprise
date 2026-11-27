# Phase 3.5 — Finite opt-in MTA monitoring run

This phase introduces `scripts/run_mta_bounded.py` as a finite local orchestration harness, not a hosted stream processor. It reuses the existing one-shot official MTA GTFS-RT connectivity, aggregate-only Kafka publishing and idempotent SQLite consumer.

- Default: `plan_only`; **no network** or Kafka I/O.
- Explicit `--execute`: 1–3 sequential cycles; 60–3600 seconds between cycles; no automatic retry.
- Each executed cycle fetches one official provider response, verifies its freshness/schema, publishes one aggregate event and invokes the existing consumer once.
- If the consumer reports a different event (possible pending backlog), the run stops with `attention_required`. The published event may remain queued and require another consumer invocation.
- Failures exit nonzero. No fake observations or automatic offset reset.
- No Kafka topic creation, no change to aviation data, no raw train/vehicle identifiers, no background scheduler.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
# Safe preview (no network or Kafka activity)
python scripts/run_mta_bounded.py --cycles 1
# Explicitly execute one genuine MTA fetch, Kafka delivery and consume attempt
python scripts/run_mta_bounded.py --cycles 1 --execute
# Optional after confirming success: at most two cycles 120 seconds apart
python scripts/run_mta_bounded.py --cycles 2 --interval 120 --execute
```

The default consumer group is shared with the Phase 3.3 one-shot consumer. If there is any backlog or another consumer running, the fetched event may not be the one consumed on that cycle. Do not reset offsets or assume exactly-once semantics end-to-end.

The dashboard continues to show stored historical observations through a protected API; **it is not a live continuously refreshing feed**. Actual operating health, consumer lag metrics, rate-limit handling, licensing review, recovery and production assurance remain future work. Production release BLOCKED 0/16.
