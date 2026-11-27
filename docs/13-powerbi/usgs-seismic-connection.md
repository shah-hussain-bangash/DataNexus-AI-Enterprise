# Power BI seismic real-data acquisition

Source: official USGS Earthquake Catalog GeoJSON API, https://earthquake.usgs.gov/fdsnws/event/1/.

One bounded historical global query, default January 2024 magnitude 4.5+, maximum 5000 events. It rejects an empty, inconsistent or limit-sized result to avoid claiming an incomplete query is complete.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/ingest_usgs_seismic.py
python scripts/ingest_usgs_seismic.py --execute
$root=(Resolve-Path .).Path
$dataOut=Join-Path $HOME "DataNexus-PowerBI-Local"
python dashboards/powerbi/Update_DataNexus_Overview.py --repo "$root" --output (Join-Path $dataOut "DataNexus_Overview_Data.json")
```

Open the existing PBIP in Power BI Desktop and refresh. The new SeismicEvents model remains empty and the seismic domain remains Not connected **until the real download and Power BI export complete**. This is neither continuous real-time streaming nor a complete multi-year big-data acquisition. Source data stays local and out of GitHub. Phase 3.13 remains paused.
