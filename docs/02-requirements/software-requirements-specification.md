# Software Requirements Specification — SRS-001
**Status:** proposed baseline; IDs are stable for traceability.

## Functional requirements
- **FR-001**: Poll approved aviation API within provider quotas; preserve source name, request timestamp and collection status.
- **FR-002**: Validate incoming event against versioned schema; quarantine malformed records.
- **FR-003**: Publish event to Kafka with stable event ID and idempotent handling.
- **FR-004**: Process event-time windows, late data and duplicates.
- **FR-005**: Persist raw immutable records and derived curated records with retention policy.
- **FR-006**: Detect defined anomaly classes and publish scored alerts with model/rule version.
- **FR-007**: Let authorized users request evidence-grounded investigation; abstain if insufficient data.
- **FR-008**: Apply per-tenant permissions at query, retrieval and tool boundaries.
- **FR-009**: Require an explicit human approval before a consequential action.
- **FR-010**: Record immutable-or-tamper-evident investigation/approval audit events.
- **FR-011**: Expose health, lag, throughput, failures, costs and AI evaluation metrics.
- **FR-012**: Offer English/Arabic UI support with verified Arabic RTL rendering.
- **FR-013**: Support deterministic replay and backup restoration with comparison checks.

## Nonfunctional targets — validate before advertising
- **NFR-001**: No unapproved cross-tenant access; demonstrated by adversarial tests.
- **NFR-002**: Initial capacity goal: 100,000 events/day, with a separate 1 million/day benchmark using explicitly labeled synthetic load.
- **NFR-003**: Initial p95 event-to-dashboard target below 60 seconds under stated test workload, excluding upstream API latency.
- **NFR-004**: Observability correlates request, event and agent IDs.
- **NFR-005**: Defined RPO/RTO targets established after infrastructure costing; restoration test required.
- **NFR-006**: Event contracts backward-compatible within each major version; breaking changes require explicit migration.
- **NFR-007**: Secrets never stored in source control, logs or issue discussions.

## Acceptance mapping
Each FR must map to a test ID and produced evidence artifact. See `traceability.csv` and `docs/11-testing-evaluation/test-strategy.md`.
