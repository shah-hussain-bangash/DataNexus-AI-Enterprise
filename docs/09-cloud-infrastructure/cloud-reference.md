# Cloud Infrastructure — CL-001
## Progressive rollout
1. Local: Docker Compose and seeded/sanitized fixtures.
2. Cloud staging: isolated network, encrypted object storage, managed identity, minimal compute, centralized logs.
3. Production candidate: Kubernetes/Terraform, policy as code, managed secrets, telemetry and release controls when justified by measurement.

## Required controls
Private subnet and ingress policy, least-privilege service identity, egress restrictions, managed key rotation, encryption at rest/in transit, workload budgets, IaC state protection and cost alerts.

## Delivery
Build → SAST/SCA and secrets scan → test → image scan/sign → staging smoke tests → controlled release → rollback test.

## Reliability
Define RPO/RTO in an ADR after recovery drills; test broker and storage outages. Avoid claiming HA merely from Kubernetes deployment.
