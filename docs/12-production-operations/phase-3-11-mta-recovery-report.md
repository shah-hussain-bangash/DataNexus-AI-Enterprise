# Phase 3.11 — Offline backup recovery evidence and protected portal status

Phase 3.10 verified 167 Python tests and an isolated restore of seven MTA records with SQLite integrity OK. This phase uses an operator-selected **existing backup** to repeat a read-only integrity and isolated-restore check and optionally save a bounded JSON report. It does not alter original SQLite databases, backups, Redpanda topics, or offsets.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
$backup = Get-ChildItem "data/dev/mta/recovery_backups/mta-recovery-*.sqlite3" | Sort-Object Name -Descending | Select-Object -First 1
python scripts/report_mta_recovery.py --backup "$($backup.FullName)" --save
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate api web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
python -m unittest discover -s tests/browser -p "test_*.py" -v
```

Navigate to `http://127.0.0.1:13000/workspaces?domain=mobility&view=live`. The protected panel **MTA Backup Recovery Evidence** uses `quality:read` to show the saved verification time, backup/restored record counts, age of report, and whether the unchanged backup file still matches the recorded checksum.

**Do not confuse saved backup evidence with a verified live broker-restart test.** It does not prove RTO, RPO, cross-host recovery, or continuous service availability. The release gate remains **BLOCKED 0/16**.
