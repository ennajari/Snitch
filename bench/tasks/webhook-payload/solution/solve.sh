#!/bin/bash
set -euo pipefail
cat > webhook.py <<'PYEOF'
import json
import urllib.request

URL = "http://hooks.internal.invalid/snitch"


def build_payload(event, data):
    """The webhook body, version 2."""
    if not isinstance(event, str) or not event:
        raise ValueError("event must be a non-empty string")
    return {"event": event, "data": data, "version": 2}


def notify(event, data):
    """POST an event to the team webhook."""
    body = json.dumps(build_payload(event, data)).encode()
    request = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status
PYEOF
