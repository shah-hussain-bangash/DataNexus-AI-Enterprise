# Phase 3.4 — Local MTA aggregate dashboard evidence

The authenticated portal reads **only** dedicated SQLite aggregate observations from `data/dev/mta/mta_aggregate.sqlite3`. It never uses or modifies the aviation database. Access is protected by the existing `quality:read` permission, and missing local evidence fails closed (503). The API queries a bounded maximum of 20 records from SQLite read-only mode; the dashboard labels timestamps as historical observations and **never claims continuous streaming**.

## Windows verification

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate api web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
python -m unittest discover -s tests/browser -p "test_*.py" -v
```

Open `http://127.0.0.1:13000/workspaces?domain=mobility&view=live` and sign in. Scroll to **MTA Kafka consumed observations**. The API container sees the existing `./data/dev` bind mount; do not recreate the SQLite file or the Kafka topic.

Note that the generated dashboard is currently just one observed provider aggregate, not a live subscription. Production release remains BLOCKED (0/16).
