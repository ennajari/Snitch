#!/bin/bash
set -euo pipefail
cat > metrics.py <<'PYEOF'
import socket

HOST, PORT = "127.0.0.1", 8125


def format_metric(name, value, tags=None):
    """One gauge line; tags sorted by key."""
    line = f"{name}:{value}|g"
    if tags:
        line += "|#" + ",".join(f"{k}:{tags[k]}" for k in sorted(tags))
    return line


def push_metric(name, value, tags=None):
    """Send one gauge to the metrics server over TCP."""
    with socket.create_connection((HOST, PORT), timeout=2) as conn:
        conn.sendall((format_metric(name, value, tags) + "\n").encode())
PYEOF
