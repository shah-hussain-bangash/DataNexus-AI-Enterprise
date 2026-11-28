# G2 authorized one-shot OpenSky verification

The local fixture replay and Power BI snapshot refresh cover the development
pipeline. Use this procedure for the first authorized live collection attempt.

## Before collecting

Confirm that OpenSky's written license covers this project's operational API
test, location, retention and intended users. Create an OAuth2 API client in
OpenSky and configure `OPENSKY_CLIENT_ID` and `OPENSKY_CLIENT_SECRET` through your
local secrets workflow. Keep the credentials out of the repository and command
history. [OpenSky license](https://opensky-network.org/about/terms-of-use) ·
[OAuth2 documentation](https://openskynetwork.github.io/opensky-api/rest.html#authentication)

Start an isolated Kafka broker and create the test topic before collecting. The
example uses the local G2 lab listener and a topic dedicated to authorized
provider data.

```powershell
python -m datanexus.cli collect --mode live --once --bootstrap 127.0.0.1:39092 --topic aviation.states.authorized.v1
```

This mode authenticates and issues one bounded states request using the configured
geographic bounds. It checks the provider timestamp against the local clock and
requires at least one normalized aircraft event. Rate limits, empty or stale
snapshots, and authentication errors end the run before any events are
published. A delivery error leaves the run unverified because Kafka may have
accepted a subset of the batch.

A successful run logs the provider snapshot time and acknowledged event count.
Process the authorized topic with a separate Spark checkpoint, Bronze path and
Iceberg warehouse. Compare the counts through the reporting layer and use an
authorized report. The fixture-only Gold exporter and the fixture Power BI
report are reserved for the isolated replay test.
