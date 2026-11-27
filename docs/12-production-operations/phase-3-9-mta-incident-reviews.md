# Phase 3.9 — MTA operator incident review evidence

Adds a **manual local review ledger** separate from Phase 3.8 alert assessment evidence. It records an operator-chosen identity, note, optional assignment, and later a resolution **assertion with an evidence reference**.

Workflow: `unreviewed → acknowledged → assigned → resolved`. All transitions are explicit CLI commands and create a new numbered JSON review entry using exclusive file creation. Previous entries and source alert assessments are never edited. A previous-record SHA-256 link detects some retrospective alterations; this is **not tamper-proof enterprise audit storage** and is not an identity service.

No API writes are exposed. An authenticated read-only `/api/v1/mta/incident-reviews` endpoint with the existing `quality:read` permission displays review status on the DataNexus dashboard. The action records are operator supplied and **do not independently prove resolution**, freshness, service restoration, or production compliance.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
# Discover existing assessment IDs without modifying them:
Get-ChildItem "data/dev/mta/alert_history/mta-alert-*.json" | Select-Object -First 5 -ExpandProperty Name
# Replace the placeholder with the SHA-256 from a previously saved alert assessment:
$digest = "<64-character-alert-assessment-digest>"
python scripts/review_mta_incident.py --assessment $digest --action acknowledge --actor operator_1 --note "Reviewed snapshot and accepted investigation"
python scripts/review_mta_incident.py --assessment $digest --action assign --actor operator_1 --assignee operator_2 --note "Assigned investigation of stale observations"
# Only after independently checking new evidence, optionally record a MANUAL resolution assertion:
# python scripts/review_mta_incident.py --assessment $digest --action resolve --actor operator_2 --note "Reviewed evidence and concluded local issue cleared" --evidence-reference "mta-monitor-YYYYMMDDTHHMMSSffffffZ.json"
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate api web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
```

Do not record resolution based on Kafka lag alone. The Phase 3.7 source freshness alert reflected *no new local ingestion after a bounded run*, not necessarily an MTA outage. This manual review feature does not alter Kafka, offsets, MTA SQLite records or aviation state. Production release **BLOCKED (0/16)**.
