# G2 aviation Gold to Power BI Desktop

This local acceptance check uses the independently verified fixture replay.
Spark reads an explicit Iceberg Gold snapshot and exports the demo tenant's
daily event and distinct-aircraft counts. The original Power BI dashboard
retains its existing aviation data.

## Export the verified fixture snapshot

From the checkout holding the local Iceberg warehouse:

```powershell
$mount = (Join-Path (Get-Location) 'pipelines\export_aviation_gold_powerbi.py') + ':/opt/project/pipelines/export_aviation_gold_powerbi.py:ro'
docker compose -p datanexus-g2-verify -f docker-compose.iceberg.yml run --rm --no-deps -v $mount iceberg-local --master 'local[2]' --conf spark.ui.enabled=false --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.9.2 /opt/project/pipelines/export_aviation_gold_powerbi.py --output /opt/project/data/replay-evidence/aviation-gold-powerbi.json
```

Use the Compose project name from your isolated replay. The exporter resolves
the current main snapshot, pins the read to its ID, verifies the count bounds
and writes one JSON file. The snapshot ID is text so consumers retain all digits.

## Validate in Power BI Desktop

Use a separate test report. In Power Query, create a text parameter
`GoldSnapshotPath` pointing to the exported file and use this query.

```powerquery
let
    Snapshot = Json.Document(File.Contents(GoldSnapshotPath)),
    Valid = if Snapshot[schema_version] = 1
        and Snapshot[source] = "local.datanexus.gold_daily_aircraft"
        and Snapshot[source_scope] = "isolated fixture replay"
        and List.Count(Snapshot[rows]) > 0
        then Snapshot else error "Unexpected aviation Gold fixture export",
    Rows = Table.FromRecords(Valid[rows]),
    Typed = Table.TransformColumnTypes(Rows, {{"date", type date}, {"events", Int64.Type}, {"aircraft", Int64.Type}}, "en-US"),
    WithSnapshot = Table.AddColumn(Typed, "snapshot_id", each Valid[snapshot_id], type text)
in
    WithSnapshot
```

Select **Home → Refresh** in Desktop. Verify that the table shows the same
snapshot ID, date, event count and daily distinct-aircraft count as the export.
The current replay produced one daily row dated 31 December 2025 with two
events and two distinct aircraft.

This is a bounded fixture check in Power BI Desktop. The authorized live
provider run and production sign-off are separate acceptance steps.
