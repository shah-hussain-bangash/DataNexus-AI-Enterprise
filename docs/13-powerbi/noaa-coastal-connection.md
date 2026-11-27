# NOAA Coastal Water Levels — verified historical hourly observations

The implementation uses NOAA CO-OPS **verified hourly_height** for The Battery, New York station **8518750** with the **MLLW** datum, metric metres, GMT, and January 1–7, 2024. NOAA explicitly documents this station/product combination. Observations are time-series heights, not tide predictions or a flood-risk score. See official docs: https://api.tidesandcurrents.noaa.gov/api/prod/ and https://tidesandcurrents.noaa.gov/stationhome.html?id=8518750 .

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/ingest_noaa_coastal.py
python scripts/ingest_noaa_coastal.py --execute
$root = (Resolve-Path .).Path
$dataOut = Join-Path $HOME "DataNexus-PowerBI-Local"
python dashboards/powerbi/Update_DataNexus_Overview.py --repo "$root" --output (Join-Path $dataOut "DataNexus_Overview_Data.json")
```

Then open `dashboards/powerbi/DataNexus_EndToEnd.pbip` in Power BI Desktop and Refresh. The new `CoastalHourly` table and `DomainCoverage` status use real validated local files only. If NOAA returns an error, empty data, incorrect timestamps, or unexpected station, the ingest fails closed and the domain stays unconnected. Source files remain local and out of GitHub. This is not continuous coastal monitoring, nor production approval; the release gate remains BLOCKED 0/16.
