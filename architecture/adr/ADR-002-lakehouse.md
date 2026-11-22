# ADR-002 — Open table-format lakehouse
**Status:** Proposed | **Date:** 2026-11-22

## Decision
Use object storage with a cataloged open table format (initial candidate: Apache Iceberg). Keep raw ingestion separate from curated, analytical datasets.

## Rationale
Separation of compute/storage, schema evolution, reproducibility, event-time analysis and ability to compare engines.

## Alternatives
Delta Lake; relational warehousing alone; managed cloud lakehouse. Final choice follows a proof-of-concept evaluating setup, throughput and maintenance cost.

## Consequences
Catalog operations, data retention, compaction, permissions and lineage become explicit responsibilities.
