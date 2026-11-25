# NYC TLC historical Bronze acquisition — first real-source milestone

This phase adds a **bounded, opt-in, offline-testable** NYC TLC public Parquet collector and displays local source-file metadata in the DataNexus dashboard. It does NOT connect MTA live feeds, parse taxi rows, publish Gold analytics, or complete production controls.

## Official source and usage

- NYC TLC dataset index: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- Public historical yellow taxi Parquet objects: https://d37ci6vzurychx.cloudfront.net/trip-data/
- Only `yellow_tripdata_YYYY-MM.parquet` for permitted months can be fetched. The source uses published trip-record data, not a streaming feed.
- Verify source licensing/terms, privacy, and applicable attribution requirements before using data beyond local evaluation.

From Windows PowerShell in the repository root:

```powershell
cd "$HOME\DataNexus-AI-Enterprise"
git pull --ff-only
python -m unittest discover -s tests -v
python scripts/ingest_nyc_tlc.py --year 2024 --month 1
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml up -d --build --force-recreate web
docker compose --env-file portal-db.env -f docker-compose.portal.yml -f docker-compose.portal.audit.yml exec web npm run lint
```

The download is **optional** and can use significant network data (up to 180 MiB for a single month). If the publisher has removed the file, moved hosting, rate-limited requests or changed its format, the command fails without claiming ingestion success. Never modify a manifest to fake acquisition.

## What gets created

- `data/dev/nyc_tlc/yellow_tripdata_2024-01.parquet` — downloaded raw source bytes.
- `data/dev/nyc_tlc/yellow_tripdata_2024-01.parquet.manifest.json` — source URL, SHA-256 digest, UTC retrieval timestamp, file size and explicit unvalidated Bronze stage.
- The API reads *only metadata*. It exposes `GET /api/v1/nyc-tlc/bronze` behind the existing local signed-session/tenant permission policy and through the Next.js route `/api/portal/nyc-tlc/bronze`.
- The dashboard's **NYC TLC — local historical acquisition** panel shows real manifest entries or a clear empty/unauthorized/backend-unavailable state.

The local `data/dev` directory is mounted read-only? No. It is a **local development volume**; this phase provides no tamper-proof object store, deduplication, validated Parquet schema or access-governed row query. A manifest is not an approved snapshot; a successful download does not prove the dataset is complete.

## Operational boundaries

- Download URL is fixed to the publisher's dataset path; no user-supplied arbitrary URL.
- Maximum downloaded file size is 180 MiB per acquisition, and existing data is never overwritten automatically.
- Basic Parquet header/footer signature checked; this is **not** schema or integrity verification of Parquet row groups. Source digest is provided for subsequent independent validation.
- No anonymous API read access, no fabricated counts, no claim of Power BI model/report or live stream availability.
- Never run `npm run build` inside the running Next.js **development** container. Use a separate clean build environment to avoid clobbering its `.next` asset tree.

## Next engineering acceptance

1. Validate full Parquet schema, date coverage, coordinates, row group integrity, dataset licensing, and reconcile monthly NYC TLC published totals when available.
2. Implement versioned Bronze/Silver/Gold Iceberg ingestion with quarantine, source lineage, idempotent processing, and data-quality reports.
3. Publish tenant-scoped historical metrics through governed reporting API and approved PostgreSQL views for Power BI.
4. Separately build MTA GTFS-Realtime collector, replay, timestamp policies, recovery tests and operational API.
5. Independent review of all security and release controls (currently BLOCKED 0/16).
