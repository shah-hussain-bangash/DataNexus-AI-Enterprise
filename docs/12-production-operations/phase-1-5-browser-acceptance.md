# Phase 1.5 — DataNexus browser UI/UX acceptance

**Scope:** real Chromium rendering and interaction, separate from the 95 Python source/unit tests. These tests do not connect data sources, approve enterprise release gates, or modify backend services.

## Run on Windows with Docker already running

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d web api
python -m pip install playwright
python -m playwright install chromium
python -m unittest discover -s tests/browser -p "test_*.py" -v
```

The acceptance tests use `http://127.0.0.1:13000` by default. Override with `DATANEXUS_BASE_URL`. Chromium screenshots for failures are written to `data/dev/browser-acceptance` (local development artifacts, not production evidence).

## Six automated browser journeys

1. Visit all seven source-domain historical views.
2. Verify 72-capability studio route, active details, Workflow and Acceptance tabs.
3. Verify 76-task roadmap shows 76/76, filters Generative AI to six tasks, finds security penetration testing, and displays unverified state.
4. Navigate the UX enhancement notification center, open command palette with Ctrl+K, search, close with Escape.
5. Open all four enterprise concept studios and verify design-fixture disclosure.
6. Verify mobile menu interaction and visible 76-task heading at 390px width.

Every test checks for uncaught browser-side JavaScript errors and saves a screenshot when a test fails.

## Manual acceptance still required

- Verify the login, permissions, and logout route with an authorized test identity; do not include credentials in artifacts.
- Visually inspect all desktop and mobile layouts, horizontal overflow, keyboard focus, accessible names and chart descriptions.
- Verify the dashboard does not fabricate measurements or present fixtures as real data.
- Test reduced-motion and contrast requirements and confirm modal focus trapping/restoration.
- Confirm the original Aviation and Dubai Property routes still render.
- Confirm no UI-only action changes backend state; verify browser network requests.
- Use an isolated staging environment for production-like build, performance, security and release review.

**Unverified until executed:** This commit adds a test harness and runbook; the author has not run the Chromium suite on the user's machine. The production release remains **BLOCKED (0/16)**.


## Phase 1.6 — Extended browser quality checks (new)

Three additional Chromium tests are included, extending the browser suite from 6 to **9 tests**:

7. Original Aviation (root) and Dubai Property routes return HTML and expose meaningful main landmarks.
8. Keyboard command palette opens with focus inside the input, traps Tab and Shift+Tab, closes on Escape and restores focus to its trigger. The UI includes a focus-trapping and restoration fix.
9. At a 390px mobile viewport, verify zero document-level horizontal overflow across the 76-task roadmap, 72-capability studio, UX Enhancements and four advanced enterprise studios.

The expanded suite **has not yet been executed on the user's Windows machine**. Browser smoke coverage does not constitute full WCAG compliance or independent production review. If an overflow or accessibility assertion fails, retain the failure screenshot, reproduce it, and fix the underlying responsive issue rather than removing the test.

### Re-run after update

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
python -m unittest discover -s tests -v
python -m unittest discover -s tests/browser -p "test_*.py" -v
```

Expected counts if all pass: **95 source/unit tests + 9 browser tests**. Release approvals remain **0/16**.
