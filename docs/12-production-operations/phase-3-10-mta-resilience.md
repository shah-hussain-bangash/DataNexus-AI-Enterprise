# Phase 3.10 — MTA resilience and isolated SQLite backup/restore

Phase 3.9 ended with one operator-reported resolution, seven stored MTA observations, committed-next-offset 7, and zero consumer lag at the final observation. Phase 3.10 provides failure-injection unit tests and **opt-in consistent SQLite snapshot backup and isolated restore verification** without changing live Kafka state.

## Test matrix (mocked broker; no actual outage)

1. Broker subscription error: no message accepted, no local store or offset commit.
2. Consumer poll error: fails rather than reporting a healthy empty queue.
3. SQLite disk/write error: offset never committed.
4. Duplicate replay after consumer restart: primary key deduplicates stored record.
5. Commit timeout: database write may be durable while offset is unconfirmed; replay remains safe. **Never report success when offset commit fails.**
6. Backup/restore: SQLite `Connection.backup()` copies a consistent snapshot even with WAL; restored record count/digest and integrity checked in isolated temp database.
7. Corrupted backup input: fail closed, no false verified result.

These are **mocked failure conditions**, NOT an actual broker outage/restart test. Production stream recovery, immutable backups, retention, encryption and enterprise disaster recovery remain outstanding.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
# Default = plan-only; no files written:
python scripts/backup_verify_mta.py
# Explicitly preserve live store and create a separately named local backup:
python scripts/backup_verify_mta.py --execute
# Optional: read-only status, does not consume Kafka:
python scripts/monitor_mta.py
```

The backup source is `data/dev/mta/mta_aggregate.sqlite3`; output is `data/dev/mta/recovery_backups`. Do not delete old backups or run reset commands. A consistent restore does NOT prove a full system RTO/RPO or broker failover.

Production release gate remains **BLOCKED (0/16)**.
