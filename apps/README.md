# DataNexus AI Enterprise Portal — Phase 3A.1

## Scope and safety
A full-stack **local engineering preview**: responsive Next.js/React frontend, FastAPI
API, read-only real SQLite event queries, map visualization, event explorer,
data-quality sample stats, export, and clearly marked not-instrumented
integrations. **No login, RBAC, public deployment or persistent audit
logging yet.** Do not expose this to the public internet. Do not load private
customer data.

Existing Kafka, Spark, Iceberg and S3 Compose setups remain separate.

**Local SQLite WAL note:** The portal mounts the development SQLite
directory writable because SQLite WAL readers may need a shared-memory file
beside the database. FastAPI still opens the database in `mode=ro` and
enables `PRAGMA query_only=ON`; no write endpoints exist. A writable bind
mount is not a production security boundary: do not deploy publicly or
use sensitive data. A production service must use a separately authorized,
least-privilege datastore.

## Quick start — Windows PowerShell
Run commands separately:

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
docker compose -f docker-compose.portal.yml config --quiet
docker compose -f docker-compose.portal.yml up -d --build
docker compose -f docker-compose.portal.yml ps
```

Open **http://127.0.0.1:13000** in your browser.

If you have previously run the local event consumer and stored events in
`data/dev/aviation.sqlite3`, the overview shows real stored event counts
and aircraft observations. If not, the dashboard shows **unconfigured**
status with zero invented records.

API `http://api:8000` is only reachable inside the Compose network and
accessed through a server-side allowlisted Next.js proxy at
`/api/portal/overview`, `/api/portal/events`, `/api/portal/quality`.

## Diagnostics
```powershell
docker compose -f docker-compose.portal.yml logs --tail 60 api
docker compose -f docker-compose.portal.yml logs --tail 60 web
docker compose -f docker-compose.portal.yml down
```
Do not use `down -v` on the existing storage stacks.

## What is real?
- SQLite-backed event listing and counts from Phase 2A, read-only
- Event search/filter/sort, row detail drawer, JSON export
- Data quality sample-only duplicate and coordinate counts
- Source timestamp and source system labeling

## What is not built?
- User authentication and RBAC: UI explicitly labels unauthenticated prototype
- Kafka/Spark/Iceberg/MinIO live health: all say *not monitored*
- ML models, GenAI and agentic workflows: labeled *coming soon*
- Live map tile service: cartographic schematic with genuine coordinate placement
- Historical trend sparklines: decorative illustration, not data (ARIA labeled)

## Upcoming gates
- Add SSO/Keycloak or production-ready identity provider and scoped roles
- Add a durable API database, migrations, tenant filtering and audit trails
- Connect authenticated live Iceberg metrics and Spark audit evidence
- Build e2e browser tests, performance budgets and accessibility review
- Add model execution/evaluation UI only after model APIs are validated
