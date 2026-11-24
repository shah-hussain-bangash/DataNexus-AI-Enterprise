"""DataNexus portal read-only operational API (Phase 3A.1).

Local prototype only: no user sessions, public deployment, or production RBAC.
"""
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from data import read_events, summarize_events

DB_PATH = os.getenv("DATANEXUS_SQLITE_PATH", "/opt/project/data/dev/aviation.sqlite3")
app = FastAPI(title="DataNexus Portal API", version="0.1.0")
# Browser requests are proxied by the Next.js server. No permissive wildcard CORS.
allowed = os.getenv("DATANEXUS_CORS_ORIGIN", "")
if allowed:
    app.add_middleware(CORSMiddleware, allow_origins=[allowed], allow_methods=["GET"], allow_headers=["Content-Type"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "datanexus-portal-api", "version": "0.1.0"}


@app.get("/api/v1/events")
def events(limit: int = Query(100, ge=1, le=500), q: str = Query("", max_length=80)):
    try:
        return read_events(DB_PATH, limit=limit, query=q)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Local event database unavailable") from exc


@app.get("/api/v1/overview")
def overview():
    try:
        return {
            "events": summarize_events(read_events(DB_PATH, limit=500)),
            "environment": "local-development",
            "systems": [
                {"name": "Kafka event backbone", "key": "kafka", "status": "not_instrumented"},
                {"name": "Spark processing", "key": "spark", "status": "not_instrumented"},
                {"name": "Iceberg / REST catalog", "key": "iceberg", "status": "not_instrumented"},
                {"name": "S3-compatible object storage", "key": "s3", "status": "not_instrumented"},
            ],
            "limitations": [
                "SQLite event counts do not indicate streaming or object-store health.",
                "Infrastructure telemetry, authentication and audit persistence are future phases.",
            ],
        }
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Local event database unavailable") from exc


@app.get("/api/v1/quality")
def quality():
    try:
        return {"events": summarize_events(read_events(DB_PATH, limit=500)),
                "checks": [
                    {"name": "Primary-key uniqueness in sampled events", "status": "sample_only"},
                    {"name": "Event coordinate availability in sampled events", "status": "sample_only"},
                    {"name": "Iceberg snapshot audit", "status": "not_connected"},
                ]}
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Local event database unavailable") from exc
