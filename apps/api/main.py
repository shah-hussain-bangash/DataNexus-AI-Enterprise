"""Local signed-session API: not production SSO or RBAC."""
import os
import sqlite3
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from auth import authenticate, require_user, TTL_SECONDS
from authorization import require_permission, require_tenant
from data import read_events, summarize_events
from source_registry import catalog as get_catalog, readiness as get_readiness
from tlc_manifest import available_downloads
from tlc_reporting import read_preview
from tlc_quality import quality_evidence
from mta_observations import read_mta_observations
from mta_monitor import latest_monitor
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
def events(limit: int = Query(100, ge=1, le=500), q: str = Query("", max_length=80), tenant_id: str | None = Query(None, max_length=100), user: dict = Depends(require_permission("aviation:read"))):
    try:
        return read_events(DB_PATH, limit=limit, query=q, tenant_id=require_tenant(user, requested_tenant=tenant_id))
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Local event database unavailable") from exc
@app.get("/api/v1/overview")
def overview(user: dict = Depends(require_permission("overview:read"))):
    try:
        return {
            "events": summarize_events(read_events(DB_PATH, limit=500, tenant_id=require_tenant(user))),
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
                "Infrastructure telemetry and immutable enterprise audit trails remain future phases.",
            ],
        }
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Local event database unavailable") from exc
@app.get("/api/v1/quality")
def quality(user: dict = Depends(require_permission("quality:read"))):
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
def audit_events(limit: int = Query(50, ge=1, le=100), user: dict = Depends(require_permission("audit:read"))):
    try:
        return {"events": recent_events(require_tenant(user), limit=limit)}
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail="Audit journal unavailable") from exc

@app.get("/api/v1/catalog")
def source_catalog(user: dict = Depends(require_permission("catalog:read"))):
    return get_catalog(require_tenant(user))

@app.get("/api/v1/readiness")
def source_readiness(user: dict = Depends(require_permission("readiness:read"))):
    return get_readiness(require_tenant(user))

@app.get("/api/v1/nyc-tlc/bronze")
def nyc_tlc_bronze(user: dict = Depends(require_permission("catalog:read"))):
    tenant = require_tenant(user)
    return {"tenant_id":tenant,"source":"nyc_tlc_yellow_taxi","state":"local_bronze_inventory_only",
            "downloads":available_downloads(os.getenv("DATANEXUS_DATA_ROOT", "/opt/project/data/dev")),
            "caveat":"Raw checksummed Parquet is NOT validated row data, Gold analytics or live data."}

@app.get("/api/v1/nyc-tlc/reporting")
def nyc_tlc_reporting(user: dict = Depends(require_permission("catalog:read"))):
    tenant = require_tenant(user)
    try:
        snapshot = read_preview(os.getenv("DATANEXUS_DATA_ROOT", "/opt/project/data/dev"))
        return {"tenant_id": tenant, **snapshot}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Local historical reporting evidence unavailable") from exc

@app.get("/api/v1/nyc-tlc/quality")
def nyc_tlc_quality(user: dict = Depends(require_permission("quality:read"))):
    tenant = require_tenant(user)
    try:
        evidence = quality_evidence(os.getenv("DATANEXUS_DATA_ROOT", "/opt/project/data/dev"))
        return {"tenant_id": tenant, **evidence}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Local historical quality evidence unavailable") from exc

@app.get("/api/v1/mta/observations")
def mta_observations(user: dict = Depends(require_permission("quality:read"))):
    tenant = require_tenant(user)
    try:
        evidence = read_mta_observations(os.getenv("DATANEXUS_DATA_ROOT", "/opt/project/data/dev"))
        return {"tenant_id":tenant, **evidence}
    except (OSError, ValueError, TypeError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503,detail="Local MTA aggregate observations unavailable") from exc

@app.get("/api/v1/mta/monitor")
def mta_monitor(user: dict = Depends(require_permission("quality:read"))):
    tenant = require_tenant(user)
    try:
        report = latest_monitor(os.getenv("DATANEXUS_DATA_ROOT", "/opt/project/data/dev"))
        return {"tenant_id":tenant,**report}
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503,detail="Local MTA monitoring evidence unavailable") from exc
