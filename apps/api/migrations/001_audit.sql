-- Development-only PostgreSQL application audit journal (P0.2)
-- Application never receives UPDATE/DELETE endpoints for this table.
CREATE TABLE IF NOT EXISTS audit_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL CHECK (event_type ~ '^[a-z][a-z0-9_]{1,63}$'),
    actor VARCHAR(100) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    outcome VARCHAR(16) NOT NULL CHECK (outcome IN ('success','failure','blocked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS audit_events_tenant_created_idx ON audit_events (tenant_id, event_id DESC);
