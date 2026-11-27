# USGS River & Watershed — modernized daily-values connector

USGS modernized OGC API v0, daily-values `/collections/daily/items`, fixed site `USGS-01491000`, parameter `00060` (discharge), statistic `00003` (daily mean), January 1–7 2024. The unit is cubic feet per second (cfs); the exporter never silently converts units or turns null discharge values into zero. No live continuous data are claimed. A request is rejected if it returns a next page, multiple daily discharge series, unexpected station, or invalid units.

USGS is migrating away from legacy `waterservices.usgs.gov/nwis/dv` endpoints, which are scheduled for decommissioning in early 2027. The modern API is recommended for new integrations.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/ingest_usgs_river.py
python scripts/ingest_usgs_river.py --execute
$root=(Resolve-Path .).Path
$dataOut=Join-Path $HOME "DataNexus-PowerBI-Local"
python dashboards/powerbi/Update_DataNexus_Overview.py --repo "$root" --output (Join-Path $dataOut "DataNexus_Overview_Data.json")
```

Then refresh the existing Power BI Desktop PBIP project. The `RiverDaily` table and river `DomainCoverage` only switch to locally connected after successful, validated real USGS acquisition. This remains a small historical query, not a big-data backfill or a continuously monitored stream. Source snapshots and manifest stay local, production approval remains BLOCKED 0/16.

Docs: https://api.waterdata.usgs.gov/docs/ogcapi/migration/ and https://api.waterdata.usgs.gov/docs/ogcapi/efficiency/
