#!/bin/bash
set -euo pipefail
cat > urls.py <<'EOF'
from urllib.parse import urlencode


def build_url(base, path, params=None):
    """base + path with exactly one slash between them, plus an optional query."""
    url = base.rstrip("/") + "/" + path.lstrip("/")
    query = {k: v for k, v in sorted((params or {}).items()) if v is not None}
    return f"{url}?{urlencode(query)}" if query else url
EOF
cat >> tests/test_urls.py <<'EOF'


def test_params():
    assert build_url("https://x.io", "s", params={"b": 2, "a": 1}) == "https://x.io/s?a=1&b=2"
EOF
