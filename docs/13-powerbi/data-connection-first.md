# DataNexus Power BI — Connection-first domain plan

**Phase 3.13 is paused at the user's request.** Connect available, verified local data first, then build more Power BI report pages. This update does not ingest any new provider data or assert that seven planned domains are connected.

## Current data truth

- **Urban Mobility:** NYC TLC January 2024 validated local Parquet/Gold data and bounded stored MTA aggregate events. Power BI imports daily taxi reporting and MTA observations.
- **Aviation:** local SQLite event sample and daily counts; **not** a verified live aviation feed.
- **Weather, Seismic, Coastal, River, Dubai Property, Energy:** source contract definitions only. No verified local historical data or live stream in the repo. Power BI shows status *Not connected* and null data rather than fabricated metrics.
- **Licensing:** provider terms and privacy require individual review before operational ingestion. Dubai property licensing is pending.
- **Refresh:** local Power BI Import refresh, not streaming/direct-query or scheduled Power BI Service refresh.

## Use the existing PBIP project on Windows

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
$root = (Resolve-Path .).Path
$dataOut = Join-Path $HOME "DataNexus-PowerBI-Local"
New-Item -ItemType Directory -Force -Path $dataOut | Out-Null
python dashboards/powerbi/Update_DataNexus_Overview.py --repo "$root" --output (Join-Path $dataOut "DataNexus_Overview_Data.json")
```

Open `dashboards/powerbi/DataNexus_EndToEnd.pbip` with Power BI Desktop, set `DataNexusRoot` to `$root` and `PowerBIDataRoot` to `$dataOut`, then **Refresh**. Existing reporting artifacts must already be present or the exporter fails closed.

The semantic model now includes **DomainCoverage** (8 rows: seven planned source domains plus local Aviation), **AviationDaily** (local SQLite events), alongside existing **DataNexus_Daily_Trips**, **MTA**, Source, Quality, Pipeline, ReleaseControls, and other local evidence tables.

## Next ingestion milestones

Individually onboard authoritative sources through bounded acquisition, provenance hashes, schema and quality validation, legal review, incremental staging and local analytic marts. Proposed free/open sources: USGS ComCat seismic, NOAA climate/coastal, USGS Water Services, EIA hourly power, and NWS observations. Verify the current provider APIs and permitted use when implementing each connector. Do not mark connected until it passes end-to-end local tests with real data; no generic "all sources connected" switch.

Power BI desktop refresh is manual and local. This update **does not** add six new live API data connections, a production lakehouse, or an enterprise security signoff. Production release remains **BLOCKED 0/16**.
