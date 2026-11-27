# Dubai Property — DLD Transactions CSV local review connector

Official Dubai Land Department site: https://dubailand.gov.ae/en/open-data/real-estate-data/

The DLD's Real Estate Data page includes a Transactions tab, date filters, and **Download as CSV**. Previous-year records are referenced at https://data.dubai. This connector never scrapes pages or circumvents access controls. An authorized operator must obtain an official CSV manually, check the applicable terms and permitted downstream reuse, and document where the file came from before considering production usage.

**Important**: importing a CSV is NOT certification of official provenance or grant of a commercial or redistributable license. The manifest sets `source_provenance_verified=false` and `license_approved=false`. The overview explicitly leaves the Dubai Property source **unverified** and excludes it from the count of verified feeds.

The importer requires official English columns `Transaction Number`, `Transaction Date`, `Transaction Type`, `Area`, `Property Type`, `Amount`. Only `Sale` / `Sales` records are aggregated; mortgage/gifts are excluded. Aggregates are by date, cadastral area and property type, and only counts and total AED are persisted, without transaction IDs, parties, or contact details. The source CSV must be preserved privately for auditor review. The importer supports CSV no larger than 60 MB and 100k rows. It rejects duplicate transaction IDs, malformed dates, invalid values, and suspicious aggregates. Do not interpret totals as covering Dubai's entire market: they cover the subset exported by the operator.

## Windows PowerShell

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/ingest_dld_transactions.py

# Download a Transactions CSV directly from the official DLD page into Downloads.
# Rename the local copy below as appropriate; source remains operator supplied.
python scripts/ingest_dld_transactions.py --csv "$HOME\Downloads\dld-transactions.csv" --execute

$root=(Resolve-Path .).Path
$dataOut=Join-Path $HOME "DataNexus-PowerBI-Local"
python dashboards/powerbi/Update_DataNexus_Overview.py --repo "$root" --output (Join-Path $dataOut "DataNexus_Overview_Data.json")
```

Do not upload sensitive original DLD CSV to public GitHub. The Power BI `PropertyDaily` table is available for **internal data review only**, pending actual rights and source confirmation. Production release is BLOCKED (0/16), Phase 3.13 paused.
