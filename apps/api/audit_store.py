"""Opt-in PostgreSQL audit journal for the local DataNexus portal.

Database operations fail closed when the audit integration is enabled.
Do not store credentials, bearer tokens, or raw user-supplied payloads.
"""
import os
import re
from datetime import datetime, timezone

VALID_EVENT = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
VALID_SUBJECT = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
VALID_TENANT = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


def enabled():
    return os.getenv("DATANEXUS_AUDIT_REQUIRED", "false").lower() == "true"


def audit_connection():
    dsn = os.getenv("DATANEXUS_AUDIT_DSN", "")
    if not dsn:
        raise RuntimeError("Audit database DSN is not configured")
    import psycopg
    return psycopg.connect(dsn, connect_timeout=5)


def initialize():
    """Create the append-only schema, idempotently, from versioned SQL."""
    from pathlib import Path
    migration = Path(__file__).with_name("migrations") / "001_audit.sql"
    with audit_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(migration.read_text(encoding="utf-8"))


def record_event(event_type, subject, tenant, outcome):
    if not enabled():
        return
    if not VALID_EVENT.fullmatch(event_type):
        raise ValueError("Invalid audit event type")
    if not VALID_SUBJECT.fullmatch(subject) or not VALID_TENANT.fullmatch(tenant):
        raise ValueError("Invalid audit subject or tenant")
    if outcome not in ("success", "failure", "blocked"):
        raise ValueError("Invalid audit outcome")
    with audit_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO audit_events (event_type, actor, tenant_id, outcome) VALUES (%s, %s, %s, %s)",
                (event_type, subject, tenant, outcome),
            )


def recent_events(tenant_id, limit=50):
    if not enabled():
        raise RuntimeError("Audit database not enabled")
    if not VALID_TENANT.fullmatch(tenant_id):
        raise ValueError("Invalid tenant")
    if not 1 <= limit <= 100:
        raise ValueError("Invalid limit")
    with audit_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT event_id, event_type, actor, tenant_id, outcome, created_at "
                "FROM audit_events WHERE tenant_id = %s ORDER BY event_id DESC LIMIT %s",
                (tenant_id, limit),
            )
            return [
                {"event_id": row[0], "event_type": row[1], "actor": row[2],
                 "tenant_id": row[3], "outcome": row[4],
                 "created_at": row[5].isoformat() if isinstance(row[5], datetime) else str(row[5])}
                for row in cursor.fetchall()
            ]
