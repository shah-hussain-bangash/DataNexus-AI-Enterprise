# Connect DataNexus sources to Power BI Desktop

The report imports validated local snapshots. The **Domain coverage** page shows
whether each domain has local data, what the proposed latest feed is, and which
sources are pending review. **Earth & water** shows weather, earthquakes, coastal
heights and river discharge. **Energy & property** shows EIA demand and Dubai
sales aggregates. The original pages show taxi and stored MTA and aviation evidence.

## Load available snapshots

Run the commands from the root of the DataNexus checkout. Reuse existing
validated snapshots. The collectors use bounded historical windows and can reject
an attempt to overwrite existing evidence.

| Domain | Snapshot used by the report | Setup |
| --- | --- | --- |
| Urban mobility | January 2024 NYC TLC reporting outputs and optional stored MTA observations | Reuse the validated TLC source, Silver, Gold and reporting outputs under `data/dev/nyc_tlc`. Reuse the MTA aggregate SQLite store when available. |
| Aviation | Local aviation event sample | Reuse `data/dev/aviation.sqlite3` when available. |
| Seismic | Bounded USGS ComCat earthquake history | [USGS seismic setup](usgs-seismic-connection.md) |
| Weather | NOAA NCEI daily observations for one station | [NOAA weather setup](noaa-weather-connection.md) |
| Coastal | NOAA CO-OPS verified hourly heights for The Battery, relative to MLLW | [NOAA coastal setup](noaa-coastal-connection.md) |
| River | USGS daily mean discharge for one monitoring site | [USGS river setup](usgs-river-connection.md) |
| Energy | EIA-930 PJM hourly demand or EIA API US48 hourly demand | Use [the keyless EIA-930 CSV](eia930-keyless-bulk.md) or [the EIA API with a local key](eia-energy-connection.md). The exporter accepts one energy snapshot at a time. |
| Dubai property | Daily Sales-group counts and AED amounts, grouped by procedure, area and property type | [Import the operator's DLD Transactions CSV](dld-observed-export-schema.md). Keep the original CSV private and keep the aggregates for internal review until source and reuse rights are confirmed. |

If the four public historical snapshots are missing, their existing collectors
can retrieve the default windows with these commands:

```powershell
python scripts/ingest_usgs_seismic.py --execute
python scripts/ingest_noaa_weather.py --execute
python scripts/ingest_noaa_coastal.py --execute
python scripts/ingest_usgs_river.py --execute
```

The source-specific guides give the date windows and station identifiers.
The NOAA daily observations cover a different scope from the planned NOAA hourly
archives and NWS latest observations. The local MTA observations and aviation
sample also cover limited historical periods.

## Regenerate the import and refresh

The exporter requires the validated NYC TLC reporting artifacts. For a new
checkout without the taxi dataset, run the existing January 2024 pipeline first.
Run each command after the preceding command succeeds.

```powershell
python -m pip install pyarrow
python scripts/ingest_nyc_tlc.py
python scripts/validate_nyc_tlc.py
python scripts/transform_nyc_tlc.py
python scripts/export_nyc_tlc_reporting.py
```

For the Power BI import, run this from
the checkout root and use your existing Power BI data folder if it differs from
the example:

```powershell
$repoRoot = (Resolve-Path .).Path
$powerBIDataRoot = Join-Path $repoRoot "data/dev/powerbi"
New-Item -ItemType Directory -Force -Path $powerBIDataRoot | Out-Null
python dashboards/powerbi/Update_DataNexus_Overview.py --repo "$repoRoot" --output (Join-Path $powerBIDataRoot "DataNexus_Overview_Data.json")
```

Once the exporter succeeds, open `dashboards/powerbi/DataNexus_EndToEnd.pbip`
in Power BI Desktop. Under **Transform data → Edit parameters**, set
`DataNexusRoot` and `PowerBIDataRoot` to the folders above. Apply the changes
and refresh. Check **Domain coverage** first, then compare the observation dates
on the charts with the dates in the source guide for each loaded snapshot.

When a local snapshot is missing, the associated chart remains empty. Dubai
property can show aggregates while provenance and licensing are still under
review. It contributes zero to the verified-feed count. Refresh is manual in
Power BI Desktop. Continuous provider collection and Power BI Service
publication require separate setup.
