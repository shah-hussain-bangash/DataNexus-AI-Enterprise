# DataNexus AI Documentation Index

Status: **architecture baseline / implementation planned**.

## Documentation domains
1. Strategy and business: vision, requirements, roadmap.
2. Requirements: SRS and traceability.
3. Enterprise architecture: context, containers, bounded contexts, ADRs.
4. Data architecture: ingestion, Kafka, lakehouse, lineage and quality.
5. Software engineering: standards, contracts and CI.
6. Generative AI: grounded multilingual RAG, LLM gateway and evaluation.
7. Agentic AI: tools, durable workflows, approvals and recovery.
8. Machine learning: training, validation, registry and monitoring.
9. Cloud infrastructure: reproducible deployment and observability.
10. Security and governance: threat models, privacy, authorization and audit.
11. Testing and evaluation: functional, adversarial, load and recovery tests.
12. Production operations: incident response, SLOs and disaster recovery.
13. Research and benchmarks: reproducible evidence and cost analysis.
14. Case studies: aviation first, financial and industrial domains later.

**Initial vertical slice:** OpenSky aviation events → ingest → validated Kafka event → lakehouse → anomaly → governed agent investigation → human review → audit and dashboard.

No production capability is claimed without running code, tests, deployment and measured evidence.
