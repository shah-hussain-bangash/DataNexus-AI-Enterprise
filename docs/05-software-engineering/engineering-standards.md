# Engineering Standards — SE-001
## Repository architecture
Documentation alongside implementation: `apps/`, `services/`, `pipelines/`, `agents/`, `models/`, `contracts/`, `infrastructure/`, `tests/`.

## Coding
Python 3.12+, type hints, structured logging, explicit exceptions, dependency isolation and pinned dependencies. TypeScript strict mode for frontend. Format/lint and scan all PRs.

## APIs and events
REST OpenAPI contracts with pagination, standardized error payloads and correlation IDs; AsyncAPI contracts for Kafka topics. Add consumer-driven contract tests. Version schemas and maintain backward-compatible migrations.

## Secure defaults
Least privilege, tenant-scoped database queries, input validation, output encoding and rate limits. Never expose raw agent tool credentials or verbose exception details.

## Tests
Unit, component, contract, integration, end-to-end, authorization, AI evaluation, load, disaster recovery. Maintain deterministic seeds and sanitized fixtures.

## Operations
Health/readiness probes, timeouts, retries with jitter, idempotency keys, circuit breakers and graceful shutdown. Prefer outbox pattern for DB-event coordination. Document every incident-class failure mode.

## Review gates
No merge with broken CI, unresolved high-severity security findings, missing contract migrations or unverified claims about production.
