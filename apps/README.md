# DataNexus AI Enterprise Portal — Phase 3A.1

## Scope and safety
A full-stack **local engineering preview**: responsive Next.js/React frontend, FastAPI
API, read-only real SQLite event queries, map visualization, event explorer,
data-quality sample stats, export, and clearly marked not-instrumented
integrations. **Local single-user sign-in exists, but enterprise SSO, MFA, multiuser RBAC, public deployment and persistent audit logging do not.** Do not expose this to the public internet. Do not load private
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
python scripts/create_portal_env.py
python -m unittest discover -s tests -v
docker compose -f docker-compose.portal.yml config --quiet
docker compose -f docker-compose.portal.yml up -d --build
docker compose -f docker-compose.portal.yml ps
```

The login/logout CSRF origin check uses the explicit `DATANEXUS_PUBLIC_ORIGIN` set in Docker Compose, not Next.js internal Docker port 3000. This local configuration only permits `http://127.0.0.1:13000`. Never disable origin validation to fix a 403.\n\nOpen **http://127.0.0.1:13000/sign-in** in your browser, using the credentials you set locally. The password is not printed or committed. If portal.env exists already, the setup script refuses to overwrite it.

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

The local prototype throttles repeated failed login attempts per username (five per five-minute window). This is memory-only, process-local hardening; it is **not** a distributed production brute-force defense. Do not use it instead of enterprise SSO, MFA, centralized rate limiting or a persistent audit trail.\n\n## What is real?
- SQLite-backed event listing and counts from Phase 2A, read-only
- Event search/filter/sort, row detail drawer, JSON export
- Data quality sample-only duplicate and coordinate counts
- Source timestamp and source system labeling

## What is not built?
- Enterprise identity and multiuser RBAC: single local account does not provide SSO or MFA
- Kafka/Spark/Iceberg/MinIO live health: all say *not monitored*
- ML models, GenAI and agentic workflows: labeled *coming soon*
- Live map tile service: cartographic schematic with genuine coordinate placement
- Historical trend sparklines: decorative illustration, not data (ARIA labeled)

## Upcoming gates
- Replace local sign-in with production identity federation, MFA, session revocation, rate limits, audit logging and scoped roles
- Add a durable API database, migrations, tenant filtering and audit trails
- Connect authenticated live Iceberg metrics and Spark audit evidence
- Build e2e browser tests, performance budgets and accessibility review
- Add model execution/evaluation UI only after model APIs are validated
