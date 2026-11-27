# Phase 3.8 — Local MTA operational alert history

Builds on Phase 3.7 warning `STORED_OBSERVATION_OLD`, verified 147/147 Python tests, six MTA aggregate records and zero Kafka lag at the saved snapshot.

This phase creates an **opt-in local immutable-style register**, one assessment file per SHA-256 of the exact saved monitoring snapshot. It never modifies Kafka, consumer groups, aviation data, or existing saved snapshots. Attempting to record the same evidence again returns the existing entry; it cannot silently change alert status to "resolved".

The authenticated portal reads at most 20 saved assessments from `data/dev/mta/alert_history` using the existing `quality:read` permission. Incident lifecycle is explicitly `unreviewed` (when alerts exist) or `not_applicable`; there is NO acknowledgement/assignment/resolution workflow. This is local operator evidence, not an immutable enterprise incident audit.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
# Generate new monitoring evidence; does not consume Kafka records:
python scripts/monitor_mta.py --save
$latest = Get-ChildItem "data/dev/mta/monitor_checks/mta-monitor-*.json" | Sort-Object Name -Descending | Select-Object -First 1
# Record a new assessment, without editing existing ones:
python scripts/register_mta_alert.py --file "$($latest.FullName)"
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate api web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
python -m unittest discover -s tests/browser -p "test_*.py" -v
```

Open `http://127.0.0.1:13000/workspaces?domain=mobility&view=live`, sign in and locate **MTA operational alert history**.

**Known limitations:** no notification delivery, no automatic remediation, no enterprise incident status transitions or external approval. This register shows only assessments explicitly recorded by an operator. The underlying evidence stays unapproved for production; release gate **BLOCKED 0/16**.
