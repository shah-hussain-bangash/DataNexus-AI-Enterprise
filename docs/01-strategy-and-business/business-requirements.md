# Business Requirements Document — BRD-001
**Status:** draft baseline.

| ID | Requirement | Acceptance evidence |
|---|---|---|
| BR-001 | Ingest approved live aviation data with rate limiting | Connector logs and provider-compliance checklist |
| BR-002 | Preserve event traceability from source to dashboard | Provenance and trace IDs |
| BR-003 | Explain anomalies using evidence and uncertainty | Agent evaluation report |
| BR-004 | Prevent unauthorized cross-tenant access | Negative authorization tests |
| BR-005 | Require human approval for consequential actions | Rejected unapproved-action tests |
| BR-006 | Display system health, quality and cost | Telemetry/dashboard evidence |
| BR-007 | Replay and recover after interruptions | Restoration exercise |
| BR-008 | Support English and Arabic UI/answers in first iteration | Bilingual acceptance tests |

### Assumptions
Provider APIs may be delayed, throttled or unavailable. Model providers have nonzero cost and quota restrictions. Demo datasets must be appropriately licensed and labeled.

### Out of scope in first milestone
Billing, automatic remediation, unrestricted text-to-SQL, petabyte-scale claims, financial execution and flight-critical decision support.
