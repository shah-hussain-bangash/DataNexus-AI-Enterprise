# G3 read-only NYC taxi metrics assistant

The local portal API accepts a fixed set of questions about the existing
January 2024 NYC Yellow Taxi report. It computes answers from the same verified
Gold snapshot as the historical reporting endpoint. This slice uses deterministic
answers and prepares the evidence contract for later model integration.

In the signed-in portal, open **Workspaces → Taxi Metrics Assistant**.
The screen offers four example questions and displays the date range, source
fields and snapshot fingerprint with each answer.

For API clients, send a signed portal bearer token and a JSON body to
`POST /api/v1/nyc-tlc/metrics-assistant`. Example request body:

```json
{"question":"Which day had the most taxi trips in January 2024?"}
```

Supported questions cover accepted trip total, busiest day, average daily trips,
and date coverage. Each answer includes the source ID, date window, Gold SHA-256
and source fields. Requests for unsupported periods, live data, arbitrary queries
or individual trips receive an unsupported response with examples and no citations.

The route uses the existing signed session and catalog permission. It accepts
neither a tenant override nor a client-supplied file or URL. Missing or modified
reporting artifacts return HTTP 503. Use the local API only and keep its bearer
token on the machine.

Run the API acceptance tests with the portal dependencies installed:

```powershell
python -m pip install -r apps/api/requirements.txt httpx
python -m unittest discover -s tests -p test_metrics_assistant.py -v
```
