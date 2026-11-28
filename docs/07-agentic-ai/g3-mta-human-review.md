# G3 local human review for MTA investigation briefs

This workflow records a human decision about a read-only investigation brief.
It does not run recovery, alter Kafka offsets, or attest to service health.

## Configure separate local identities

The existing administrator signs in and submits a brief. Configure a second
local account through `DATANEXUS_MTA_REVIEWER_USERNAME` and
`DATANEXUS_MTA_REVIEWER_PASSWORD_HASH` in the portal API environment. Generate
the reviewer's salted PBKDF2 hash with `auth.hash_password`, using a private
password different from the administrator's. Keep both identities and hashes
in the existing local secret configuration. Without a distinct reviewer, the
decision route remains inaccessible.

## Submit and decide

Use the existing `/auth/login` endpoint for each identity separately and supply
the resulting bearer token to the appropriate request.

1. As administrator, POST `{"assessment_sha256":"<alert assessment digest>"}`
   to `/api/v1/mta/review-requests`. The response contains the fixed action,
   frozen evidence, evidence SHA-256, request ID and an expiry one hour later.
2. As reviewer, GET `/api/v1/mta/review-requests/{request_id}` and read the
   frozen brief. POST `{"decision":"approve","evidence_sha256":"<digest from the request>"}`
   or the corresponding `reject` choice to
   `/api/v1/mta/review-requests/{request_id}/decision`.
3. Verify the recorded choice, reviewer identity and decision timestamp. A
   repeated identical decision returns the original record. A conflicting
   decision, changed evidence or an expired request returns HTTP 409.

The API re-reads the cited local evidence before recording a new decision.
Request and decision records are kept in `mta/human_review.sqlite3` below the
configured DataNexus data root. A concurrent decision is serialized by SQLite.
This milestone verifies the local two-identity API. Enterprise identity,
independent audit retention and recovery execution remain separate work.
