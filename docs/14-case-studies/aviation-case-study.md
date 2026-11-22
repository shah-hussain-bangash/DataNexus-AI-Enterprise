# Aviation Intelligence Case Study — CS-001
**Planned scenario:** ingest publicly accessible aircraft states under source license, calculate regional traffic and aircraft telemetry quality indicators, detect unusual data patterns, and open a human-reviewed AI investigation.

## Safety boundary
Not for air traffic control or aviation safety intervention. No assertion that a signal is an actual aircraft fault without validated domain evidence.

## Demonstration workflow
Provider request → connector telemetry → event envelope → Kafka → processing → curated lakehouse → anomaly → authorized investigation → cited report → review → audit.

## Evidence to publish
Data-license review, architecture, screenshots of live ingestion, replay demonstration, schema tests, permission tests, latency benchmark, cloud cost and known limitations.
