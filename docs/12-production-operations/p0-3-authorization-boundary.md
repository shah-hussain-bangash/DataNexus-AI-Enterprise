# P0.3 — Local API permission boundary and tenant checks

**Status: local policy hardening only.** This is *not* production-ready
enterprise identity, SSO, MFA, multi-user RBAC, or approved tenant isolation.

## What this change does

- Adds explicit server-side permissions for aviation observations, overview,
  data quality, and the PostgreSQL audit endpoint.
- Rejects roles that have no defined permission, even if a future handler
  were to pass an unexpected user dictionary.
- Rejects malformed or missing tenant identity and denies a requested tenant
  that differs from the verified session tenant.
- All SQLite event reads still scope to the authenticated tenant with
  parameterized SQL queries; optional audit reads use the same tenant.
- Adds source-contract tests and preserves existing portal routes.

A UI tab is not authorization. FastAPI evaluates every permission at the
endpoint. No new user accounts, roles or tenant-switching controls are
presented because these are not yet implemented or verified.

## Run on Windows

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build api
```

Use your existing credentials. Do **not** regenerate `portal.env` or
`portal-db.env`, and do not delete Docker volumes.

## Remaining production requirements

Choose a real OIDC or SAML identity provider, enforce MFA, validate issuer
and audience, implement centrally managed multi-user RBAC, authorization
negative tests against running services, consistent tenant scoping across
Kafka/Spark/Iceberg/PostgreSQL, privileged DB roles, session revocation and
immutable audit logging. No release gate is satisfied by this update alone.
