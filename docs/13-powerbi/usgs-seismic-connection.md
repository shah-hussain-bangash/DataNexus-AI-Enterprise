# Power BI seismic real-data acquisition

Source: official USGS Earthquake Catalog GeoJSON API, https://earthquake.usgs.gov/fdsnws/event/1/.

One bounded historical global query, default 2024-01-01 through 2024-01-08 (one week) magnitude 4.5+, maximum 5000 events. It rejects an empty, inconsistent or limit-sized result to avoid claiming an incomplete query is complete.

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

## If the provider still returns an error

The collector now displays metadata count and actual returned feature count separately. USGS's endtime is documented as inclusive; a smaller requested window is used here to simplify troubleshooting. Do not treat an error as a connected data source, and do not delete any existing snapshots. Try `python scripts/ingest_usgs_seismic.py --start 2024-01-08 --end 2024-01-15 --execute` only if the default window fails; every request remains bounded and separately named.

## USGS GeoJSON metadata compatibility

Provider responses can contain a valid `features` array without `metadata.count`. The validator accepts the missing optional field but continues validating each event, unique identifiers, UTC time bounds, numeric ranges, and the 5000-result query ceiling. If `metadata.count` is present, a malformed value or disagreement with the returned feature count is rejected. Successful acquisition and a subsequent Power BI export are both required before considering seismic locally connected.
