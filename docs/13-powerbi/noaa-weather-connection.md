# NOAA Weather & Climate — first local historical station connection

This connector uses the documented official NOAA NCEI Access Data Service daily-summaries dataset: `https://www.ncei.noaa.gov/access/services/data/v1`. The historical test window is January 2024, using station `USW00094728`, `TMAX`, `TMIN`, and `PRCP` with metric units. Station/day is the observation grain; missing measurements stay NULL, not zero. This is **not** the NOAA hourly GHCN archive, nor an active NWS stream. The observed and stored data are local only.

NOAA currently warns that migration of some services to cloud infrastructure may cause API availability issues. Do not bypass failed validation or invent values.

Windows PowerShell:

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/ingest_noaa_weather.py
python scripts/ingest_noaa_weather.py --execute
$root = (Resolve-Path .).Path
$dataOut = Join-Path $HOME "DataNexus-PowerBI-Local"
python dashboards/powerbi/Update_DataNexus_Overview.py --repo "$root" --output (Join-Path $dataOut "DataNexus_Overview_Data.json")
```

Once the export succeeds, open `dashboards/powerbi/DataNexus_EndToEnd.pbip` and refresh. The new `WeatherDaily` table is imported; its `weather_daily` inventory is empty and the weather domain remains *Not connected* until a real validated NOAA acquisition succeeds. No credentials, raw responses, or Power BI caches are committed to GitHub. Release gate remains BLOCKED 0/16.

Provider documentation: https://www.ncei.noaa.gov/access/search/documentation/data-service/
