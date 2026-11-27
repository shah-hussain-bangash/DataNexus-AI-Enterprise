# Phase 3.6 — Read-only MTA lag and freshness monitoring

Phase 3.5 verified five finite real MTA producer → Redpanda → SQLite cycles, but did not establish continuous streaming. Phase 3.6 adds an **operator-triggered, read-only** monitor and a protected view of its saved snapshot.

Monitor behavior:
- Queries **only** `mta.subway.updates.v1` (partition 0) and consumer group `datanexus-mta-aggregate-v1`.
- Computes Kafka lag as high watermark minus committed next offset, but **unknown/uncommitted or expired offsets never count as zero lag**.
- Separately reads the last persisted MTA provider timestamp from the dedicated SQLite database and calculates age at check time.
- No MTA API call, no Kafka consumption or commits, no data or topic modification.
- `--save` creates a *new* local evidence JSON without overwriting existing files.
- Dashboard endpoint `/api/v1/mta/monitor` requires an authenticated user with `quality:read`, returns the latest operator snapshot, labels it stale if older than 5 minutes, and does not call Kafka itself.

## Windows verification

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
# Read-only inspection, no new evidence file
python scripts/monitor_mta.py
# Explicitly save one evidence snapshot for the dashboard
python scripts/monitor_mta.py --save
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate api web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
python -m unittest discover -s tests/browser -p "test_*.py" -v
```

Then sign into `http://127.0.0.1:13000/workspaces?domain=mobility&view=live` and inspect the panel **MTA Kafka lag and freshness — local snapshot**. A saved monitor snapshot becomes stale after five minutes; use a new `--save` instead of treating old values as current.

Caveats: only the declared single-partition local topic is supported. The monitor does not establish upstream MTA availability, a consumer SLA, replay recovery, failure alerting or a production audit. No production approvals are implied. Release gate remains BLOCKED (0/16).
