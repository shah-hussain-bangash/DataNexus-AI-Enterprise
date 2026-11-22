# Phase 2 Runbook — Aviation Streaming Foundation
**Status:** Implemented as a local reference workflow, not independently verified on a deployed broker.

## Scope and limitations
OpenSky REST is polled, not push streaming. Redpanda provides a Kafka-compatible local broker. The consumer persists idempotent records to SQLite; this is **not** a distributed Spark/Flink lakehouse. Phase 2b must add an object-store table format, DLQ, metrics and scaling tests.

## Requirements
Python 3.11+, Docker with Compose, local machine with adequate free memory. Never commit an OpenSky client secret.

## Run local broker
```bash
docker compose up -d redpanda
python -m pip install -e '.[kafka]'
```
Wait until broker starts; check `docker compose logs redpanda`.

Terminal A:
```bash
python -m datanexus.cli consume
```
Terminal B (offline fixture, no external API credentials):
```bash
python -m datanexus.cli collect --mode fixture
```
SQLite path: `data/dev/aviation.sqlite3`. Inspect with a local SQLite client. Re-running fixture should not increase the number of unique events.

## Optional live aviation source
Review OpenSky API terms and credits, create OAuth2 client credentials, set `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET`; run:
```bash
python -m datanexus.cli collect --mode live --interval 120
```
A small Dubai-area bounding box is the default. This connector respects 429 retry headers, but it does not independently enforce a strict daily credit budget. Stop collection before quota exhaustion. Handle potential commercial-use and redistribution restrictions before uploading collected data.

## Test
```bash
python -m unittest discover -s tests -v
```
Tests use fixtures and require no network or broker.

## Verification still required
- Broker integration / restart and offset recovery test
- Poison record → dead-letter queue policy and quarantine
- Event schema compatibility and retention policies
- Object storage + Iceberg/Delta table with partitioning
- Process monitoring, traces and cost
- Live source permission and rate-accounting tests
- Load / throughput / latency and backup restoration

**Safety:** Aviation signals are for analytical research only, not operational flight decisions.
