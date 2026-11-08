import json
import urllib.request

URL = "http://hooks.internal.invalid/snitch"


def notify(event, data):
    """POST an event to the team webhook."""
    body = json.dumps({"event": event, "data": data}).encode()
    request = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status
