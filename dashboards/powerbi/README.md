# DataNexus Power BI overview

The editable Power BI project opens on **All data**, a single page with nine
charts across eight domains. The other pages provide source coverage, pipeline
assurance and detailed views by domain.

Open `DataNexus_EndToEnd.pbip` in Power BI Desktop. Set the `DataNexusRoot` and
`PowerBIDataRoot` Power Query parameters to your local folders, then refresh.
DataNexusRoot defaults to `C:\DataNexus-AI-Enterprise`. PowerBIDataRoot defaults
to `C:\DataNexus-PowerBI-Local`. Neither folder nor any imported data is uploaded.

The taxi queries use the repository's local January 2024 reporting snapshot.
Run `Update_DataNexus_Overview.py --repo <local-repository> --output
<PowerBIDataRoot>/DataNexus_Overview_Data.json` before refreshing platform evidence.
Existing validated taxi artifacts are prerequisites. The exporter is read-only.

## Save-to-GitHub on the authoring computer

Save changes in the `.pbip` project, not the separate `.pbix` snapshot.
`PowerBI_GitHub_Sync.py --source <authoring-folder> --state <local-state-folder>
--watch` waits for a stable save, copies only allowlisted project definitions,
replaces computer-specific data paths with parameters, then commits and pushes
this folder through an isolated checkout using existing Git credentials.

The watcher never stages other DataNexus changes, uploads credentials or data,
or force-pushes. Authentication/network/conflict failures retain pending changes
and are recorded in the local sync status. Start it again after resolving errors.
Automatic uploads require the authoring computer to be running and online.

## Deliberately local

PBIX/PBIT files, `.pbi` caches, local settings, JSON evidence snapshots, CSV,
SQLite and Parquet data, credentials and logs are excluded. This source project
can open without its data cache; refresh requires your local datasets.

Stored MTA observations and the aviation sample are historical evidence.
Planned sources and unverified runtime services are labelled. Reporting integrity
does not imply production approval. No live provider collection or cloud Power BI
publication is configured by this folder.

## Connect and view all domains

Follow the [local connection and refresh guide](../../docs/13-powerbi/data-connection-first.md)
to load the available historical snapshots into Power BI Desktop. The coverage
page shows which local snapshots are available and the status of each proposed
latest feed. Dubai property is shown for internal review when an operator supplies
a CSV. Missing snapshots leave their report visuals empty.
