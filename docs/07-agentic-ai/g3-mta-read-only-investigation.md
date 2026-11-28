# G3 read-only MTA incident investigation

An authenticated operator with the existing quality permission can request
`GET /api/v1/mta/investigation`. The API selects the newest actionable record
in the 50-entry local alert reader window. To select a particular record from
that window, pass its lowercase SHA-256 as `assessment_sha256`. Unknown or
non-actionable IDs return 404.

The brief uses the validated alert record, hash-linked operator review and
local SQLite restore evidence. Each source includes a timestamp and a
reference. Alert reasons and operator notes remain in their original evidence
records. A prior resolution is shown as an operator assertion. A successful
isolated restore provides context for review and does not establish that the
provider or broker recovered for this incident.

A missing assessment yields `insufficient_evidence`; invalid or inaccessible
artifacts fail closed with HTTP 503. Check the returned gaps before recording a
human decision in the existing review ledger. The investigation endpoint reads
evidence and produces a brief. Recovery execution and approval workflows
remain separate milestones.
