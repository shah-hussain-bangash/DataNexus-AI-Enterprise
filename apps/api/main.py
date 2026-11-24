"""Local signed-session API: not production SSO or RBAC."""
import os
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from auth import authenticate, require_user, TTL_SECONDS
from data import read_events, summarize_events
DB_PATH = os.getenv("DATANEXUS_SQLITE_PATH", "/opt/project/data/dev/aviation.sqlite3")
app = FastAPI(title="DataNexus Portal API", version="0.2.0")
class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)
@app.get("/health")
def health():
    return {"status": "ok", "service": "datanexus-portal-api", "version": "0.2.0"}
@app.post("/auth/login")
def login(payload: LoginRequest):
    try:
        token = authenticate(payload.username, payload.password)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Local sign-in not configured") from exc
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
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
