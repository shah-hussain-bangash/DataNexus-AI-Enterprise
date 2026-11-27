# EIA-930 keyless bulk CSV import (historical batch)

EIA's official six-month BALANCE CSV files contain hourly demand and additional operating metrics by balancing authority. This first bounded connector selects **PJM, 2024-01-01 through 2024-01-07 UTC** from the **2024 Jan-Jun** file; it deliberately does **not** claim to represent aggregate US48 demand or a live streaming feed. It reads demand only, records the CSV SHA-256 and provenance, and exports locally to the existing Power BI `EnergyHourly` table. EIA states that demand is an integrated hourly value, reported in MW on its CSV; for each hourly period the numerical energy equivalent is MWh.

Official documentation: https://www.eia.gov/electricity/930-content/about.html

CSV file reference: https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_2024_Jan_Jun.csv

1. Download the CSV from EIA Hourly Grid Monitor > Download Data > Six-Month Files > 2024 > Balance. Do not rename the file. If the website returns a 503, do not bypass its access controls; retry later or use an appropriately licensed official redistribution.
2. Save the CSV to `$HOME\\Downloads\\EIA930_BALANCE_2024_Jan_Jun.csv`.
3. Run below PowerShell commands separately:

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/ingest_eia930_bulk.py
python scripts/ingest_eia930_bulk.py --csv "$HOME\Downloads\EIA930_BALANCE_2024_Jan_Jun.csv" --execute
$root=(Resolve-Path .).Path
$dataOut=Join-Path $HOME "DataNexus-PowerBI-Local"
python dashboards/powerbi/Update_DataNexus_Overview.py --repo "$root" --output (Join-Path $dataOut "DataNexus_Overview_Data.json")
```

The importer does not initiate an HTTP request or require an API key. It validates the source filename, CSV field names, PJM identity, hourly UTC timestamps, finite demand, uniqueness, minimum observations, maximum 168 hours, and integrity of the local snapshot. No overwrite. If the original file cannot be downloaded, leave the feed **unconnected**, not simulated.

The existing EIA v2 API connector remains available but should not be used with a compromised credential. Keep Phase 3.13 paused and release BLOCKED (0/16).
