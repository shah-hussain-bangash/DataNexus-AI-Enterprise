"""Local signed-session API: not production SSO or RBAC."""
import os
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from auth import authenticate, require_user, TTL_SECONDS
from data import read_events, summarize_events
from login_throttle import throttle, WINDOW_SECONDS
from audit_store import enabled as audit_enabled, initialize as initialize_audit, record_event, recent_events
DB_PATH = os.getenv("DATANEXUS_SQLITE_PATH", "/opt/project/data/dev/aviation.sqlite3")
app = FastAPI(title="DataNexus Portal API", version="0.2.1")

@app.on_event("startup")
def startup_audit():
    if audit_enabled():
        initialize_audit()

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)
@app.get("/health")
def health():
    return {"status": "ok", "service": "datanexus-portal-api", "version": "0.2.0"}
@app.post("/auth/login")
def login(payload: LoginRequest):
    # Process-local backoff only; production identity must enforce distributed limits.
    if throttle.saturated(payload.username):
        record_event("auth_blocked", payload.username, os.getenv("DATANEXUS_ADMIN_TENANT", "demo"), "blocked")
        raise HTTPException(status_code=429, detail="Too many login attempts", headers={"Retry-After": str(WINDOW_SECONDS)})
    remaining = throttle.retry_after(payload.username)
    if remaining:
        record_event("auth_blocked", payload.username, os.getenv("DATANEXUS_ADMIN_TENANT", "demo"), "blocked")
        raise HTTPException(status_code=429, detail="Too many login attempts", headers={"Retry-After": str(remaining)})
    try:
        token = authenticate(payload.username, payload.password)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Local sign-in not configured") from exc
    if not token:
        record_event("auth_login", payload.username, os.getenv("DATANEXUS_ADMIN_TENANT", "demo"), "failure")
        throttle.failure(payload.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    record_event("auth_login", payload.username, os.getenv("DATANEXUS_ADMIN_TENANT", "demo"), "success")
    throttle.success(payload.username)
    return {"access_token": token, "token_type": "bearer", "expires_in": TTL_SECONDS}
@app.get("/auth/me")
def me(user: dict = Depends(require_user)):
    return user
@app.get("/api/v1/events")
def events(limit: int = Query(100, ge=1, le=500), q: str = Query("", max_length=80), user: dict = Depends(require_user)):
    try:
        return read_events(DB_PATH, limit=limit, query=q, tenant_id=user["tenant_id"])
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Local event database unavailable") from exc
@app.get("/api/v1/overview")
def overview(user: dict = Depends(require_user)):
    try:
        return {
            "events": summarize_events(read_events(DB_PATH, limit=500, tenant_id=user["tenant_id"])),
            "environment": "local-development",
            "workspace": {"role": user["role"], "tenant_id": user["tenant_id"], "username": user["username"]},
            "systems": [
                {"name": "Kafka event backbone", "key": "kafka", "status": "not_instrumented"},
                {"name": "Spark processing", "key": "spark", "status": "not_instrumented"},
                {"name": "Iceberg / REST catalog", "key": "iceberg", "status": "not_instrumented"},
                {"name": "S3-compatible object storage", "key": "s3", "status": "not_instrumented"},
            ],
            "limitations": [
                "SQLite counts do not indicate streaming or object-store health.",
                "Local single-user sessions are not enterprise SSO or multiuser RBAC.",
                "Infrastructure telemetry and persistent security audit trails are future phases.",
            ],
        }
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Local event database unavailable") from exc
@app.get("/api/v1/quality")
def quality(user: dict = Depends(require_user)):
    try:
        return {"events": summarize_events(read_events(DB_PATH, limit=500, tenant_id=user["tenant_id"])),
                "checks": [
                    {"name": "Primary-key uniqueness in sampled tenant events", "status": "sample_only"},
                    {"name": "Coordinate availability in sampled tenant events", "status": "sample_only"},
                    {"name": "Iceberg snapshot audit", "status": "not_connected"},
                ]}
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Local event database unavailable") from exc

@app.get("/api/v1/audit")
def audit_events(limit: int = Query(50, ge=1, le=100), user: dict = Depends(require_user)):
    try:
        return {"events": recent_events(user["tenant_id"], limit=limit)}
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail="Audit journal unavailable") from exc
