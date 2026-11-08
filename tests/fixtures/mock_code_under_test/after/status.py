import json
import urllib.request


def fetch_status(base_url="http://localhost:8099", timeout=5):
    with urllib.request.urlopen(f"{base_url}/health", timeout=timeout) as response:
        return json.load(response)["status"]
