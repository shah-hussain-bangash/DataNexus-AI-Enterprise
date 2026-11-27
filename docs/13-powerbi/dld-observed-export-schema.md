## Actual DLD export schema update — 27 November 2026

An operator uploaded a file named `transactions-2026-11-27.csv` with 22 headers including `TRANSACTION_NUMBER`, `INSTANCE_DATE`, `GROUP_EN`, `PROCEDURE_EN`, `AREA_EN`, `PROP_TYPE_EN`, and `TRANS_VALUE`. This official-site-shaped export contains 9,711 source rows dated November 1–27, 2026, with one exact repeated transaction row. The importer now accepts both the earlier illustrative English schema and this observed real export schema; it removes only exact duplicate rows and rejects differing rows with the same ID. It aggregates by **date, procedure, area, property type**. Different sale procedures are not merged into completed sales. It never writes transaction IDs, buyer/seller counts, or person-level records into Power BI output.

These results are not a claim of complete Dubai market coverage, or confirmation of licensing, or authorization to publish. The source CSV remains private and must be stored under allowed retention controls.

For the new real CSV run on Windows:

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/ingest_dld_transactions.py --csv "$HOME\Downloads\transactions-2026-11-27.csv" --execute
$root=(Resolve-Path .).Path
$dataOut=Join-Path $HOME "DataNexus-PowerBI-Local"
python dashboards/powerbi/Update_DataNexus_Overview.py --repo "$root" --output (Join-Path $dataOut "DataNexus_Overview_Data.json")
```

This importer keeps provenance and licensing review pending and deliberately does **not** increment the verified-source counter.
