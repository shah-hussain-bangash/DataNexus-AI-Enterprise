# Agentic Architecture — AA-001
## Agents
- Alert triage: summarizes anomaly context, read-only.
- Evidence investigator: executes scoped retrieval and query tools.
- Risk reviewer: checks incomplete evidence and policy constraints.
- Report composer: prepares traceable recommendation for humans.

## Workflow state machine
RECEIVED → VALIDATED → INVESTIGATING → EVIDENCE_READY → REVIEW_PENDING → APPROVED/REJECTED → CLOSED. Failures transition to RETRY_WAIT or MANUAL_REVIEW; retries are bounded.

## Tool control
Deny by default. Read-only tools initially. Every call carries tenant scope, trace ID, permission context and execution limit. Reject unsafe prompts in external event payloads.

## Human approval
Reviewers approve a specific action, payload hash and evidence snapshot. Expired or modified plans invalidate approval. No self-approval or reuse after changed evidence.

## Recovery and audit
Checkpoint durable state, idempotency keys, reconciliation before retrying uncertain external effects, and append-only audit events. Test duplicate execution, tool timeout, stale approval and cross-tenant requests.
