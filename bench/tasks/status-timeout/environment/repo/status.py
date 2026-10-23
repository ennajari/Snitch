import json
import urllib.request

SERVICE_URL = "http://localhost:8099"


def fetch_status(base_url=SERVICE_URL):
    """GET <base_url>/health and return its JSON "status" field."""
    with urllib.request.urlopen(f"{base_url}/health") as response:
        return json.load(response)["status"]
