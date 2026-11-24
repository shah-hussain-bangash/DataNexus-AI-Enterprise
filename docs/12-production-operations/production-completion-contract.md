# DataNexus — End-to-End Production Completion Contract

**Status: NOT PRODUCTION READY.** This repository currently contains a verified
local event pipeline, lakehouse experiments, a local FastAPI/Next.js portal,
single-user signed sessions, and 33 passing Python contract/unit tests reported
by the developer. That is not evidence of enterprise security, reliability, or
a validated production deployment.

## Definition of done

A production release is permitted only when all 16 gates pass, their underlying
artifacts are independently reviewed, and an accountable owner signs the final
release decision. The automated gate checks **evidence metadata, not truth**;
a misleading evidence file cannot make an unsafe implementation safe.

1. **Identity** — production OIDC/SAML SSO, MFA, identity lifecycle, session
   revocation and credential rotation; unauthorized access tests.
2. **Authorization** — server-enforced RBAC/ABAC, tenant isolation across all
   queries and jobs, row-level isolation, cross-tenant negative tests.
3. **Ingestion** — provider authorization, schema contracts, retry/backpressure,
   idempotency, DLQ, replay and observable lag.
4. **Streaming** — restart/replay recovery, checkpoint durability, latency
   and exactly-once/idempotent sink evidence.
5. **Lakehouse** — verified Bronze/Silver/Gold lineage, Iceberg snapshots,
   compaction/retention, schema evolution, integrity audits.
6. **API** — versioned auth-protected APIs, threat modeling, CORS/CSRF,
   rate limits, bounded queries, input validation and security tests.
7. **ML** — real training and inference services, versioned datasets/models,
   baselines, drift monitoring and reproducible offline/online evaluation.
8. **GenAI/RAG** — licensed evidence corpora, retrieval evaluation,
   prompt-injection resistance, citation fidelity and safety evaluation.
9. **Agents** — least-privilege tools, bounded actions, explicit human approval,
   immutable audit evidence and negative/abuse case tests.
10. **Observability** — logs, traces, metrics, health checks, dashboards,
    incident alerts with real incident-response exercise.
11. **Supply chain** — no committed secrets, managed secret store, pinned
    images/dependencies, SBOM, vulnerability scanning, signed releases.
12. **Recovery** — encrypted automated backups, restore drills, defined
    RTO/RPO and recorded recovery exercise.
13. **Performance** — realistic workload and stress tests with error,
    saturation, throughput, latency and cost budgets.
14. **Deployment** — segregated dev/stage/prod, infrastructure as code,
    TLS, continuous delivery, canary and rollback test.
15. **Compliance** — provider terms, data residency/privacy, retention and
    deletion implementation, access-review evidence.
16. **End-to-end** — licensed aviation source to Kafka to Spark to Iceberg
    to ML/GenAI/agent approval to dashboard and audit trail, validated using
    genuine authorized data and failure injection.

## Engineering sequence — no additional cosmetic redesign

**P0 / system foundations:** Lock baseline, production-ready architectural
decisions, identity/security boundaries, dedicated PostgreSQL metadata store,
real CI build/typecheck/security checks, deployment model and environment
separation. Keep existing Phase 2 and Phase 3 development environments working.

**P1 / reliable platform:** Authenticated data ingestion, replay and durable
lakehouse storage, tested end-to-end, plus query APIs and observability
rather than isolated smoke tests.

**P2 / AI platform:** Reproducible ML train/serve/monitor, grounded RAG with
evaluations, policy-constrained agent workflows and real human approvals.

**P3 / production operations:** Secure cloud deployment, continuous delivery,
audit, alerting, SLOs, capacity and disaster recovery, performance, penetration
tests and release sign-off.

## Gate usage

Run locally:
```powershell
cd "$HOME\DataNexus-AI-Enterprise"
python scripts/release_gate.py
python scripts/release_gate.py --json
```

The command is **expected to exit 1 and say BLOCKED** until production
implementation and external validation are complete. Do not suppress or
remove failed controls merely to obtain a green result.

Evidence belongs under the Git-ignored `production-evidence/` directory:
```json
{
  "control": "identity_sso_mfa",
  "result": "pass",
  "environment": "production",
  "approved_by": "release-reviewer",
  "verified_at": "2026-11-24T00:00:00Z",
  "artifact_sha256": "64_hex_characters_of_independently_reviewed_artifact"
}
```

Never create an evidence file just to satisfy a test. The underlying
test report, incident drill, scan, deployment logs and review record must
exist, be archived securely and match the given SHA-256. Evidence metadata
is not a substitute for a real production security or reliability review.

## Unresolved deployment decisions

- Authorized cloud account, domain, TLS and production DNS.
- Azure/AWS/GCP platform choice, organization policies and budgets.
- Identity provider and enterprise user/tenant definitions.
- Licensed production aviation data source, retention and residency.
- SLOs, RTO/RPO, incident-response owners and deployment approvals.

These are external ownership decisions, not inputs to guess or hardcode.
