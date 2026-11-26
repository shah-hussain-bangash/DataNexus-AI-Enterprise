# Phase 2.3 — Protected local historical Gold reporting

The Phase 2.2 local Silver and Gold Parquet outputs are prerequisites. This milestone creates a **bounded metadata/Gold-only JSON snapshot**, authenticated FastAPI endpoint and visible dashboard panel. This is NOT production reporting, live telemetry or commercial redistribution.

## Windows

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/export_nyc_tlc_reporting.py --input data/dev/nyc_tlc/silver_gold_2024_01
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate api web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
python -m unittest discover -s tests/browser -p "test_*.py" -v
```

Inspect `data/dev/nyc_tlc/silver_gold_2024_01/reporting_preview.json` locally. Never commit local Parquet, raw records or reporting snapshots. The exporter refuses to overwrite an existing report: review and intentionally archive before regenerating.

Visit `http://127.0.0.1:13000/workspaces?domain=mobility&view=historical`. The **Local NYC TLC Gold reporting** panel reads `/api/portal/nyc-tlc/reporting` using the existing signed-session cookie and backend permission. A missing or modified report displays unavailable, never fabricated values. This is local single-admin permission and **not** enterprise multi-tenant isolation.

The reporting snapshot retains **all actual Gold dates** but separately reports `in_month_trip_count` and `outside_month_trip_count`. Gold's 35 pickup dates need not all be January. No February pickup is silently attributed to January. The amounts in `total_amount_sum` are trip total values in the source file (USD), not net business revenue.

Prerequisite data source and reporting snapshot files are integrity checked. No new external connectivity, Power BI dataset, stream, licensing approval, production business signoff or 16 release controls are asserted.
