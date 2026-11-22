# Generative AI Architecture — GA-001
## Workloads
Bilingual English/Arabic investigation summaries, natural-language analytics and evidence-grounded retrieval. Add other languages only with appropriate evaluation datasets.

## Gateway
Central model routing with approved models, per-tenant quotas, timeouts, fallback, prompt template versioning, cost recording and redaction. Log metadata rather than raw sensitive prompts by default.

## Retrieval
Tenant-filtered retrieval over curated documents, metadata and approved analytic summaries. Cite source IDs, time windows, and query scope. Reject unsupported claims; abstain when source confidence or permissions fail.

## Governed text-to-SQL
Only reviewed read-only query templates or schema-constrained query construction against allowlisted views. Enforce tenant row filters at DB level, query ceilings and inspection before execution. No arbitrary SQL execution by agents.

## Evaluation
Groundedness, answer correctness, citation support, cross-tenant leakage, prompt injection, Arabic evaluation, latency and cost. Version datasets and report failures honestly.
