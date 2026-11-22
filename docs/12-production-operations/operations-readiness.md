# Production Operations — OP-001
**Not production-ready until the following are demonstrated.**

## SLOs and operational ownership
Define ingestion freshness, successful event processing, query availability, dashboard latency and AI workflow completion. Set alert thresholds after measuring baselines.

## Observability
OpenTelemetry distributed traces, structured logs with redaction, service metrics, broker lag, data quality, model evaluation and cost dashboards.

## Incident runbooks
Provider outage/rate limit; stuck consumer group; schema incompatibility; lakehouse sink failure; compromised credential; agent retry storm; data deletion request.

## Backup and DR
Version datasets, encrypt backups, restore PostgreSQL/state, reconstruct materialized views, replay Kafka when allowed, and rehearse RTO/RPO. Document evidence from actual drills.

## Release readiness
Change approval, staged rollout, smoke tests, rollback runbook, incident contacts, license review and security sign-off.
