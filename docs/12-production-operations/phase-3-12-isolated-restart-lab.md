# Phase 3.12 — Independent Redpanda restart lab

The test uses **a second Docker Compose project** and volume, localhost **29092**, synthetic Kafka topic `datanexus.mta.restart.lab.v1`, and test-only group `datanexus-mta-restart-lab-v1`. It never touches the existing MTA Kafka topic, its last committed-next-offset 7, the seven stored MTA aggregates or the aviation pipeline.

The operator explicitly restarts **only** `redpanda-lab`. The preparation script publishes and commits a synthetic offset 0, recording committed-next-offset 1. After restart it verifies event persistence, group offset continuity, and a new event at offset 1. It does NOT automatically restart containers and cannot cryptographically attest that the operator actually restarted the broker. The metadata connection duration is not downtime, RTO or service recovery duration.

## Windows PowerShell — follow exactly

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
# Confirm separate Compose project and exposed port first:
docker compose -f docker-compose.mta-restart-lab.yml config
python scripts/mta_restart_lab.py --phase plan
# Start isolated broker without touching normal docker-compose.yml:
docker compose -f docker-compose.mta-restart-lab.yml up -d
# Wait until broker is ready; then explicitly prepare:
python scripts/mta_restart_lab.py --phase prepare
# Only this isolated service is restarted:
docker compose -f docker-compose.mta-restart-lab.yml restart redpanda-lab
# After broker is responsive again:
python scripts/mta_restart_lab.py --phase verify
# Check your original broker separately, read-only:
python scripts/monitor_mta.py
```

If the lab topic/state file already exists, the prepare command refuses reinitialization. Do not delete volumes, reset offsets, or use `docker compose down -v` as a workaround. Preserve the lab evidence and use a deliberate isolated lab reinitialization plan for any future run. The lab may consume additional local Docker resources; stop only the lab with `docker compose -f docker-compose.mta-restart-lab.yml stop` if needed.

**Limitations:** single-node dev broker, single test topic/partition, no failover quorum, no live broker outage, no measured end-to-end recovery SLA, no production DR certification. Production release remains **BLOCKED 0/16**.
