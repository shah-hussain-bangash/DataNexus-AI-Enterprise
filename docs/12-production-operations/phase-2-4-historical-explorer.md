# Phase 2.4 — Interactive historical reporting on real Gold data

This milestone adds a **client-side historical analytics explorer** to the existing authenticated local NYC TLC Gold reporting panel.

## Controls

- Choose real Gold-derived metrics: daily accepted taxi-trip count, sum of trip distance (miles), or sum of trip total values (USD, **not** business net revenue).
- Select start/end pickup dates, defaulting to January 2024.
- Optionally include out-of-month pickup dates, which remain explicitly labeled.
- View chart, reconciled selected-range KPIs and exact daily table.
- Pick a date in the table and reset filters.
- Empty-range states and reversed date-range warnings are explicit.

Data is served by the existing protected `/api/portal/nyc-tlc/reporting` path. No fabricated trend lines, production provenance, live feeds, Power BI integration or backend mutation are added. Chart is accessible via textual summary and full data table. The existing design fixture charts elsewhere in the application remain clearly marked.

## Run on Windows

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
python -m unittest discover -s tests/browser -p "test_*.py" -v
```

Visit `http://127.0.0.1:13000/workspaces?domain=mobility&view=historical` and inspect **Local NYC TLC Gold reporting**. If API snapshot evidence is missing, the visualization stays unavailable instead of displaying invented values.

Release status remains BLOCKED 0/16. Source license review is still pending.
