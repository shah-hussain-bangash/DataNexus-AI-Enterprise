"""Rate-conscious OpenSky API client with OAuth2 credentials and 429 handling."""
import json
import os
import time
from urllib import parse, request, error

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
API_URL = "https://opensky-network.org/api/states/all"


class OpenSkyRateLimited(RuntimeError):
    def __init__(self, retry_seconds):
        super().__init__(f"OpenSky rate limit: retry after {retry_seconds} seconds")
        self.retry_seconds = retry_seconds


class OpenSkyClient:
    def __init__(self, client_id=None, client_secret=None, opener=None):
        self.client_id = client_id if client_id is not None else os.environ.get("OPENSKY_CLIENT_ID", "")
        self.client_secret = client_secret if client_secret is not None else os.environ.get("OPENSKY_CLIENT_SECRET", "")
        self.opener = opener or request.urlopen
        self._token = None
        self._expiry = 0

    def token(self):
        if not self.client_id or not self.client_secret:
            return None  # anonymous access is limited and may be unavailable
        if self._token and time.time() < self._expiry:
            return self._token
        data = parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }).encode()
        req = request.Request(TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        with self.opener(req, timeout=20) as response:
            payload = json.load(response)
        self._token = payload["access_token"]
        self._expiry = time.time() + max(60, int(payload.get("expires_in", 1800)) - 120)
        return self._token

    def states(self, bbox):
        lamin, lomin, lamax, lomax = bbox
        if not (-90 <= lamin < lamax <= 90 and -180 <= lomin < lomax <= 180):
            raise ValueError("invalid geographic bounding box")
        query = parse.urlencode({"lamin": lamin, "lomin": lomin, "lamax": lamax, "lomax": lomax})
        headers = {"User-Agent": "DataNexusAI-Research/0.1"}
        token = self.token()
        if token:
            headers["Authorization"] = "Bearer " + token
        req = request.Request(API_URL + "?" + query, headers=headers)
        try:
            with self.opener(req, timeout=30) as response:
                return json.load(response)
        except error.HTTPError as exc:
            if exc.code == 429:
                raw = exc.headers.get("X-Rate-Limit-Retry-After-Seconds", "300")
                try:
                    delay = max(60, min(int(raw), 86400))
                except ValueError:
                    delay = 300
                raise OpenSkyRateLimited(delay) from exc
            if exc.code == 401:
                self._token = None
                self._expiry = 0
            raise
