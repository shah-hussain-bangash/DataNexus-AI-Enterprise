# ADR-001 — Kafka event backbone
**Status:** Proposed | **Date:** 2026-11-22

## Context
Support asynchronous, replayable, partitioned events from external sources and future enterprise connectors.

## Decision
Use Apache Kafka as the first event backbone with versioned payloads and explicit idempotency. Compare managed Kafka and Azure Event Hubs later for operational cost.

## Alternatives
Direct HTTP processing lacks durable replay; Redis Streams is simpler but a different ecosystem; cloud queues are managed but may complicate multi-domain replay.

## Consequences
Need broker operations, quotas, DLQ, partition strategy, consumer lag alerts and incident runbooks. Adoption remains provisional until validated.
