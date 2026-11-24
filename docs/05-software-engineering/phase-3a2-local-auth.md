# Phase 3A.2 — Local Sign-in + Tenant-scoped API

## Delivered
- Premium, responsive two-panel sign-in UI and sign-out actions
- One local administrator initialized interactively, with PBKDF2-HMAC password hash
- Short-lived HMAC-signed bearer tokens, held in HttpOnly SameSite=Strict browser cookie
- Authenticated FastAPI overview, quality, aviation-events and identity endpoints
- SQLite tenant restriction enforced in SQL, with parameterized queries
- Next.js server-side proxy that checks the session cookie and passes a bearer token internally
- No password or signing secret committed to GitHub

## Windows setup (PowerShell)
```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python scripts/create_portal_env.py
python -m unittest discover -s tests -v
docker compose -f docker-compose.portal.yml config --quiet
docker compose -f docker-compose.portal.yml up -d --build
```

Create a new **strong** local password when prompted. The setup writes an
untracked `portal.env`. Keep it private, never paste its contents into chat.
If it already exists, the script **refuses to overwrite**.

Open http://127.0.0.1:13000/sign-in, enter the username/password you chose,
and confirm the real aviation records display. Use Sign Out in the sidebar.
Try an incorrect password and verify the error is generic. After logout,
`curl.exe -i http://127.0.0.1:13000/api/portal/overview` should return HTTP 401.

## Limitations
This is **local single-user security practice**, not enterprise-ready identity.
It lacks MFA, centralized identity federation, rate limiting, durable session
revocation, immutable audit logging and multiuser role administration.
The API uses development SQLite data; do **not** expose this portal publicly.

No Kafka/Spark/Iceberg live health or model/agent execution is implied.
Previously verified Phase 2A–2G services are preserved as separate stacks.

## Recovery
If login fails, inspect:
```powershell
docker compose -f docker-compose.portal.yml logs --tail 60 api
docker compose -f docker-compose.portal.yml logs --tail 60 web
```
Do not delete the Kafka or MinIO volumes.
