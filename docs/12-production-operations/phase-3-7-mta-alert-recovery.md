# Phase 3.7 — Local MTA alert assessment and recovery drill contracts

Phase 3.6 verified the operator snapshot: six persisted MTA aggregates, Kafka committed-next-offset 6 and high watermark 6, zero pending Kafka messages **at the time of that check**, with the last stored observation ~34 minutes old. Phase 3.7 adds *offline advisory rules*, not autonomous recovery.

## Alert rules

- `MONITOR_STALE`: saved monitoring check older than 300 seconds.
- `STORED_OBSERVATION_OLD`: last stored provider timestamp was older than 300 seconds **at the time of snapshot**; this is not proof the provider is unavailable.
- `CONSUMER_BACKLOG`: lag of 1–9 records gives warning; 10+ gives critical. Thresholds are local development defaults, not production SLOs.
- `OFFSET_UNKNOWN`: missing, expired or impossible offsets give critical, never misleading zero-lag status.
- Contradictory metrics or source timestamps fail closed.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/monitor_mta.py --save
$latest = Get-ChildItem "data/dev/mta/monitor_checks/mta-monitor-*.json" | Sort-Object Name -Descending | Select-Object -First 1
python scripts/assess_mta_alerts.py --file "$($latest.FullName)"
```

Optional CI-style exit codes: `python scripts/assess_mta_alerts.py --file "$($latest.FullName)" --strict` returns 2 when any threshold alerts exist. Alerts are **advice**, not proof of actual outage or automatic action.

## Controlled recovery drills (non-destructive)

A. Run the existing unit tests for malformed messages: invalid messages are not committed by the consumer.
B. Run `python scripts/consume_mta_aggregate.py --timeout 5` after checking your existing topic. A `no_event_available` response is expected with zero lag; do not delete or reset topic offsets.
C. If an operator finds backlog, consume **one** event, then run `python scripts/monitor_mta.py --save` again to observe changes. Never assume a consumer read of an older event confirms a newly published event.

Known gaps: no Kafka outage/restart integration drill, push notifications, automated retries, scheduling, or enterprise incident response. Maintain existing protected monitoring dashboard; no auto-remediation. Release gate remains **BLOCKED 0/16**.
