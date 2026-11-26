# Phase 2.5 — Local NYC TLC Data Quality and Browser Verification

Adds a dedicated read-only quality evidence endpoint `/api/v1/nyc-tlc/quality` protected by the existing signed session and `quality:read` permission, proxied at `/api/portal/nyc-tlc/quality`.

The panel reports source/Silver/quarantine reconciliation, acceptance and rejection percentages, warning categories, out-of-month trips, and elapsed **historical export age** (NOT live freshness). It rejects missing evidence, mismatched counts, altered Gold/Silver hashes, and invalid timestamps. No reporting assets or raw source files are modified. Validation warning counts may overlap and should not be summed into rejected row counts.

Browser Test 10 intercepts the signed reporting endpoint with **explicitly synthetic fixture rows** to test actual chart/filter behavior; it is NOT real data verification. Browser Test 11 confirms absent sessions do not reveal historical charts. These require local Docker and Playwright.

## Windows commands

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate api web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
python -m unittest discover -s tests/browser -p "test_*.py" -v
```

Visit `http://127.0.0.1:13000/workspaces?domain=mobility&view=historical`, authenticate, and inspect **NYC TLC historical quality monitoring**. Note: local single-admin auth is not production SSO/tenant-isolation proof. Release remains BLOCKED 0/16.
