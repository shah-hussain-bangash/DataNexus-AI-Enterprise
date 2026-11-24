# Phase P0.2 — Optional PostgreSQL audit journal

This is a **local engineering increment, not production-grade compliance auditing**.

The pre-existing portal continues using tenant-scoped read-only SQLite for
aviation events. PostgreSQL is introduced independently for operational audit
records. There is no migration, deletion or relabeling of existing aviation data.

## Set up once in Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python scripts/create_portal_db_env.py
python -m unittest discover -s tests -v
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build
```

The command must include `--env-file portal-db.env` so Compose can interpolate
the generated database password into the private container-to-container DSN.
The password is **never printed**. Do not paste either environment file or the
result of `docker compose config` into chats or issue trackers: the latter
may expand and reveal secrets.

The API initializes the audit table on startup whenever the integration is
enabled. Verify with:

```powershell
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml ps
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml logs --tail 30 api
```

**Avoid printing `portal-db.env` or `DATANEXUS_AUDIT_DSN`.**

After signing in, read audit metadata from the authenticated backend using
the browser's session through the Next.js server proxy after it is exposed.
For now the API provides a tenant-filtered `GET /api/v1/audit` endpoint
which is intentionally **not available through the public Next.js proxy**.
That limits accidental exposure of audit records in the local UI.

To stop optional stack while retaining data:

```powershell
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml down
```

Never run `down -v`: it deletes named volumes, including PostgreSQL data.

## What is captured

- Local sign-in success, failure, and blocked attempts (actor, tenant, outcome).
- No plaintext password, bearer token or arbitrary request body.
- Append-only application API (no update/delete endpoint).
- Tenant-filtered audit query API, restricted to authenticated admin.
- Fail-closed login when required audit persistence cannot be reached.

## Important gaps

- Database-owner credentials and DB-admin role are shared with application;
  PostgreSQL privileges and immutability guarantees still need separation.
- Authentication throttling is process-local, not distributed.
- No enterprise OIDC/SSO, MFA, RBAC, immutable external audit sink,
  backup verification, retention policy or independent audit approval.
- Only login events are persisted; broader data/API/admin actions remain future.
- This does not satisfy any of the 16 production-release controls by itself.

## Operational note

If you use `docker compose -f docker-compose.portal.yml up -d` without the
optional override, PostgreSQL audit logging is not enabled. Do not treat the
local SQLite and PostgreSQL stores as interchangeable.
