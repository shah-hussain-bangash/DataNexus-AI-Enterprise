# EIA Energy Grid: historical hourly electricity demand

The EIA API v2 endpoint `electricity/rto/region-data/data` supports grid demand. This connector selects `respondent=US48` and `type=D`, January 1–7, 2024, hourly UTC, with at most 1000 rows per request. The normalized metric retains **megawatthours per hourly interval**; the Power BI model does not invent actual MW capacity, emission factors, or generation data. This is *one* regional demand measure, not all energy-grid operations.

The official EIA API requires a **free API key**. Register: https://www.eia.gov/opendata/register.php. Keep your key on your Windows machine; never paste it into ChatGPT or push it to GitHub.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/ingest_eia_energy.py
# Enter your EIA API key on your own computer when prompted (not in chat):
$env:EIA_API_KEY = Read-Host "Enter EIA API key"
python scripts/ingest_eia_energy.py --execute
Remove-Item Env:EIA_API_KEY
$root=(Resolve-Path .).Path
$dataOut=Join-Path $HOME "DataNexus-PowerBI-Local"
python dashboards/powerbi/Update_DataNexus_Overview.py --repo "$root" --output (Join-Path $dataOut "DataNexus_Overview_Data.json")
```

Then open `dashboards/powerbi/DataNexus_EndToEnd.pbip` and refresh. `EnergyHourly` remains empty and energy `DomainCoverage` remains not connected until your local EIA download and validation succeed.

The Python code must not log the authenticated URL or key. The manifest contains only a public, key-free query. No automatic live subscription or production release approval is implied. The release gate remains BLOCKED 0/16.
