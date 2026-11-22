# Test & Evaluation Strategy — TE-001
## Test levels
- Unit: schema, normalization, deduplication, anomaly rules.
- Integration: real broker, object storage and service contracts.
- E2E: external sample → dashboard and audited approval with correlation IDs.
- Security: tenant isolation, unauthorized tools, prompt injection, stale approvals, secrets.
- Resilience: upstream throttling, broker restart, model provider timeout, sink failure, replay, restore.
- Performance: throughput, lag, p95 event-to-dashboard latency, cost.
- AI quality: groundedness, citations, Arabic handling, refusal/abstention and tool safety.

## Evidence discipline
Each test links requirement IDs, commit SHA, environment, data provenance, configuration, run command, expected/actual outcome and known limitations. Do not mark planned tests as passing.

## Critical exit criteria
Zero known critical cross-tenant bypass; unauthorized actions rejected; deterministic replay; audited approvals; tested rollback and backup restoration before production claims.
