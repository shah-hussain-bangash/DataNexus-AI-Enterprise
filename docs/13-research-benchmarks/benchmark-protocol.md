# Benchmark Protocol — BM-001
## Goal
Produce reproducible, honest performance evidence for the streaming and AI workflows.

## Workloads
W1 genuine licensed upstream aviation data within quota; W2 synthetic load for scaling. Never mix them into one real-data claim.

## Measures
Events/second, bytes/second, Kafka lag, end-to-end p50/p95/p99, failure/loss/duplicate rates, per-event storage cost, resource usage, AI answer groundedness, agent successful recovery and approval safety.

## Procedure
Record hardware, cloud SKU/region, software versions, test data source, event size distribution, partition counts, number of workers, warm-up, load shape, repetitions and confidence intervals. Publish scripts and raw sanitized results.

## Acceptance
No metric is advertised until a run is completed; report adverse results and limitations alongside improvements.
