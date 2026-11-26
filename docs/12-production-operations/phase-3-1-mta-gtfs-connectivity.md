# Phase 3.1 — MTA subway GTFS-Realtime connectivity (one-shot, read-only)

Initial external source: Metropolitan Transportation Authority subway GTFS-Realtime, **A/C/E** feed (alternatively numerical 1–7 routes). Official developer source: https://api.mta.info/. The provider says it does not require API keys for these realtime feeds.

The script performs **exactly one opt-in HTTPS request**, using a fixed allowlist of official MTA host/feed URLs, a 20-second request timeout, 5 MiB maximum response, redirect rejection, and Google's GTFS-Realtime protobuf schema. It verifies required protobuf fields, feed timestamp, age classification, unique entity IDs, and counts entity types. It records only an aggregate response SHA-256 and counts, **never vehicle/trip IDs or raw protobuf**. Stale feeds over two hours are labeled stale rather than represented as current.

This **does not** continuously poll, publish Kafka events, store raw Bronze events, implement replay/offset recovery, expose a verified live UI, certify data licensing, or satisfy production approvals. If the provider response fails validation, no success report is written.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m pip install gtfs-realtime-bindings
python -m unittest discover -s tests -v
python scripts/collect_mta_gtfs.py --feed ace --output data/dev/mta/live_checks
```

The output report resides under ignored `data/dev/mta/live_checks`. It contains response timestamp, SHA-256, byte count, entity counts, freshness, and caveats. Never push local payloads or observations to public GitHub. Do not rerun rapidly or use automatic high-frequency polling. For provider errors (HTTP 403, 429, unrecognized protobuf, stale feed), share the sanitized error message; do not work around rate limits.

**Next:** after verifying a real response and terms of use, establish a carefully scoped, opt-in Kafka producer with separate topic, deduplication, retry/backoff, provenance and operational safety evidence. Not done in 3.1.

Release status remains BLOCKED 0/16.
