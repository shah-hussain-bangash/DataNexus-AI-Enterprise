# Enterprise Architecture — EA-001
**Reference approach:** ISO/IEC/IEEE 42010 viewpoints, C4 diagrams, bounded contexts and ADRs.

## Context and bounded contexts
1. **Ingestion** — upstream adapters, provider licensing/quota controls, source health.
2. **Event processing** — Kafka topics, schema validation, replay and deduplication.
3. **Lakehouse** — raw/curated storage, lineage, governance and retention.
4. **Analytics/ML** — feature definitions, scoring, evaluation and versioning.
5. **AI control plane** — model gateway, retrieval, durable agent execution and approval.
6. **Experience/API** — dashboard, user queries, reporting and tenant-bound authorization.
7. **Platform/security** — identity, policies, deployment, observability and recovery.

## Key architectural decisions
Kafka is selected provisionally as the event backbone (ADR-001). An open table-format lakehouse is proposed (ADR-002). Keep provider APIs behind adapters to permit substitution.

## Deployment progression
Local docker compose for a reproducible vertical slice → single cloud staging environment → Kubernetes only after measurable operational need. Multi-region/high availability are not claimed without tests.

## Trust boundaries
External event providers, public API edge, message backbone, storage, model provider and agent tools are separate trust zones. Explicit authorization and data minimization at each crossing.

## C4 diagrams
See `architecture/c4/system-context.mmd` and `architecture/c4/container-view.mmd`.

## Failure scenarios
Upstream rate limiting; malformed schema; duplicate or late event; Kafka unavailability; lakehouse sink interruption; model timeout; poisoned documents; lost reviewer session; stale approval; cross-tenant query.
