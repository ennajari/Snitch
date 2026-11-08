#!/bin/bash
set -euo pipefail
cat >> textstats.py <<'PYEOF'


def title_case(text):
    """Each word capitalised, the rest lowercased; spacing kept."""
    return " ".join(w[:1].upper() + w[1:].lower() for w in text.split(" "))
PYEOF
