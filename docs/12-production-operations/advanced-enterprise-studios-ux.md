# DataNexus enterprise UI/UX studios — iteration 2026-11-25

This milestone expands the **existing /workspaces** page with four dedicated **UI-only** product experiences:

1. **Power BI Studio** — report selector, metric placeholders, visual and period controls, semantic-model design, refresh/security/lineage journeys.
2. **AI & Agents** — locally simulated grounded Q&A that safely abstains, model registry/evaluation concepts, incident investigation journey, local human-approval simulation.
3. **Security Center** — identity, MFA, role and tenant access preview, license/privacy/data lineage screens, and proposed threat controls.
4. **Operations Center** — service topology, unavailable telemetry placeholders, incident template explorer, sixteen-release-control design, recovery and deployment concept screens.

Every feature is a **design prototype**. No Power BI API, AI model endpoint, authentication-policy change, alert source, agent action, secret rotation, backup restoration, deployment, or production service was connected in this iteration. The page continues to show the real local backend evidence and NYC TLC Bronze inventory elsewhere. The existing Aviation and Dubai Property routes remain untouched.

## Run on your Windows development computer

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
```

Open:

- http://127.0.0.1:13000/workspaces?view=powerbi-studio
- http://127.0.0.1:13000/workspaces?view=ai-studio
- http://127.0.0.1:13000/workspaces?view=security-studio
- http://127.0.0.1:13000/workspaces?view=operations-studio
- http://127.0.0.1:13000/workspaces?view=capabilities

## Visual browser acceptance remaining

Test desktop and mobile viewports, keyboard-only navigation, tab changes, filter selection, no fabricated values, no accidental backend side effects, screen-reader names, color contrast, and browser console/network errors. Run an independent production Next.js build separately from the running dev container to avoid conflicting .next assets.

**Production release remains BLOCKED 0/16**. UI/UX screen availability does not complete the 72 acceptance requirements or certify a production system.
