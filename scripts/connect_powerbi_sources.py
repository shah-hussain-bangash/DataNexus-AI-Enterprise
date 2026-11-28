"""Prepare the six additional DataNexus sources for a Power BI Desktop refresh."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

import ingest_dld_transactions as property_data
import ingest_eia930_bulk as energy_bulk
import ingest_eia_energy as energy_api
import ingest_noaa_coastal as coastal
import ingest_noaa_weather as weather
import ingest_usgs_river as river
import ingest_usgs_seismic as seismic


REPO = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = REPO / "data" / "dev" / "powerbi"
EXPORTER = REPO / "dashboards" / "powerbi" / "Update_DataNexus_Overview.py"


def public_snapshot(module, folder, end, local_only):
    snapshot = module.load(REPO / folder)
    if snapshot is None and not local_only:
        module.fetch("2024-01-01", end, folder=REPO / folder)
        snapshot = module.load(REPO / folder)
    return snapshot


def energy_snapshot(args):
    bulk_folder = REPO / energy_bulk.ROOT
    api_folder = REPO / energy_api.ROOT
    bulk = energy_bulk.load(bulk_folder)
    api = energy_api.load(api_folder)
    if bulk is not None and api is not None:
        raise ValueError("Both EIA snapshots exist. Select one using the energy setup guide.")
    if bulk is not None or api is not None or args.local_only:
        return bulk if bulk is not None else api
    if args.eia_csv is not None:
        energy_bulk.import_csv(args.eia_csv, folder=bulk_folder)
        return energy_bulk.load(bulk_folder)
    if os.environ.get("EIA_API_KEY"):
        energy_api.fetch("2024-01-01", "2024-01-07", folder=api_folder)
        return energy_api.load(api_folder)
    return None


def property_snapshot(args):
    folder = REPO / property_data.ROOT
    snapshot = property_data.load(folder)
    if snapshot is None and args.dld_csv is not None and not args.local_only:
        property_data.ingest(args.dld_csv, folder=folder)
        snapshot = property_data.load(folder)
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--power-bi-data-root", type=Path, default=DEFAULT_DATA_ROOT,
        help="Folder used for the PowerBIDataRoot parameter in Power BI Desktop.",
    )
    parser.add_argument("--eia-csv", type=Path, help="Local EIA930_BALANCE_2024_Jan_Jun.csv.")
    parser.add_argument("--dld-csv", type=Path, help="Private local DLD Transactions CSV.")
    parser.add_argument("--local-only", action="store_true", help="Validate existing snapshots without acquiring new data.")
    args = parser.parse_args()
    if args.local_only and (args.eia_csv is not None or args.dld_csv is not None):
        parser.error("--local-only cannot be used with CSV imports")

    sources = (
        ("Earthquakes", lambda: public_snapshot(seismic, seismic.OUT, "2024-01-08", args.local_only)),
        ("Weather", lambda: public_snapshot(weather, weather.ROOT, "2024-01-31", args.local_only)),
        ("Coastal water levels", lambda: public_snapshot(coastal, coastal.ROOT, "2024-01-07", args.local_only)),
        ("River discharge", lambda: public_snapshot(river, river.ROOT, "2024-01-07", args.local_only)),
        ("Energy grid", lambda: energy_snapshot(args)),
        ("Dubai property", lambda: property_snapshot(args)),
    )
    ready = 0
    for name, load_source in sources:
        try:
            snapshot = load_source()
        except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
            print(f"{name}: import failed ({type(error).__name__}). See the source setup guide.", flush=True)
            continue
        if not snapshot or not snapshot["records"]:
            print(f"{name}: no validated local rows.", flush=True)
            continue
        ready += 1
        review = " (internal review)" if name == "Dubai property" else ""
        print(f"{name}: {len(snapshot['records']):,} local reporting rows{review}.", flush=True)

    print(f"{ready}/{len(sources)} sources have local reporting rows.", flush=True)
    data_root = args.power_bi_data_root.resolve()
    result = subprocess.run(
        [sys.executable, str(EXPORTER), "--repo", str(REPO), "--output", str(data_root / "DataNexus_Overview_Data.json")],
        cwd=REPO,
        check=False,
    )
    if result.returncode:
        print("Power BI export failed. Check the exporter error and the local taxi artifacts.", file=sys.stderr)
        return 1

    print(f"DataNexusRoot: {REPO}")
    print(f"PowerBIDataRoot: {data_root}")
    print("Open DataNexus_EndToEnd.pbip and refresh it in Power BI Desktop.")
    return 0 if ready == len(sources) else 2


if __name__ == "__main__":
    raise SystemExit(main())
