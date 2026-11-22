# Data Platform Architecture — DA-001
## Event path
OpenSky adapter → validation → Kafka raw topic → stream transform → curated lakehouse and anomaly topic → governed query APIs.

## Ingestion
Use bounded geographic queries, provider quotas, exponential backoff and explicit polling timestamps. Do not claim a polled API is native push streaming. Respect provider retention and redistribution terms.

## Event envelope
`event_id`, `schema_version`, `source`, `source_event_time`, `ingested_at`, `tenant_id`, `trace_id`, `payload`. Validate and quarantine invalid envelopes. See `contracts/schemas/`.

## Kafka semantics
Partition by appropriate stable entity key. Treat delivery as at-least-once unless proven otherwise; make downstream writes idempotent. Define retention and dead-letter topic. Record consumer lag and replay behavior.

## Lakehouse
Bronze: immutable provenance-rich ingestion. Silver: validated, normalized and deduplicated data. Gold: analytic materializations. Partition by event date and domain; register schema versions and lineage. Document retention and deletion exceptions.

## Quality checks
Freshness, completeness, schema compliance, null rates, geospatial bounds, late-event rate, duplicates and drift. Publish quality metrics and block invalid data from affecting automated decisions.

## Scaling
Baseline: 100k events/day target. Benchmark separately at 1M/day synthetic load. Never claim petabyte-ready performance without validated cost, scale and recoverability.
