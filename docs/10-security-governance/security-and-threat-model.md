# Security & AI Governance — SG-001
## Assets
External licensed data, tenant information, model prompts/responses, credentials, event pipelines, audit evidence and human approvals.

## Threats
Prompt-injection in retrieved content; cross-tenant retrieval; malicious SQL; secret exposure; event poisoning; replay/duplicate actions; stale approvals; supply-chain compromise; denial of service and logging sensitive content.

## Controls and tests
Authentication/authorization at each boundary; DB row-level policy; agent tool allowlists; evidence-bound approvals; encryption, secret rotation, dependency scanning; retention policies; minimum audit fields. Adversarial test every isolation and approval boundary.

## Governance
Map AI use cases to risk owners, prohibited autonomous actions, model cards, evaluation records and human override. Use NIST AI RMF, OWASP ASVS and LLM guidance as design references, not certification claims.

## UAE
Evaluate applicable UAE privacy and sector-specific rules for actual data and deployment location with qualified counsel. Do not assume blanket compliance.
