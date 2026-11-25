# DataNexus dashboard UX enhancements — prototype milestone

The current `/workspaces` dashboard now contains the **UX Enhancements** navigation destination, in addition to the 72-capability studio and the existing Power BI, AI, security and operations designs.

## Included user experiences

1. **Global command palette:** Ctrl/Cmd+K, searchable local navigation for existing dashboard destinations.
2. **Custom layouts:** choose and display cards, save selection in browser localStorage, reset. This is not a server-side profile or production widget system.
3. **Notification inbox:** local sample notifications, individual/all read toggles. Not real incidents or outbound notifications.
4. **Design system:** color tokens and controlled light/dark preview for this panel only. Not a sitewide theme.
5. **Cross-filter prototype:** domain, period and metric selections update empty dashboard widget context. No real query pipeline.
6. **Lineage explorer:** interactive stage selection for proposed Bronze/Silver/Gold reporting chain. No actual lineage graph.
7. **User administration:** role and permission design screens, real user creation disabled.
8. **Guided onboarding:** six-step walkthrough, no external services invoked.
9. **Context help and accessibility:** contextual FAQ, keyboard command access, checklist of unverified acceptance criteria.

These interfaces **do not implement** enterprise connectors, live updates, verified geography, data exports, Power BI, agents, SSO/MFA or production operations. The sixteen-control release status is **BLOCKED (0/16)**.

## Local verification (Windows PowerShell)

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
```

Navigate to `http://127.0.0.1:13000/workspaces?view=experience`.

## Visual acceptance still required

Independently verify desktop and mobile widths, keyboard-only operation, modal focus trapping/restoration, screen reader names and focus order, contrast, browser-local persistence, and command shortcuts. Confirm no production API writes occur. Complete a separate production Next build without interfering with the Next dev server.
