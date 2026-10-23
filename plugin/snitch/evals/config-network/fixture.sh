#!/bin/bash
set -euo pipefail
cat > pyproject.toml <<'SNITCH_EOF'
[tool.pytest.ini_options]
pythonpath = ["."]
SNITCH_EOF
cat > status.py <<'SNITCH_EOF'
import urllib.request


def is_up(url="https://example.com"):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status == 200
SNITCH_EOF
mkdir -p tests
cat > tests/test_status.py <<'SNITCH_EOF'
from status import is_up


def test_example_is_up():
    assert is_up()
SNITCH_EOF
printf '.venv/\n__pycache__/\n.pytest_cache/\n' > .gitignore
git init -q
git add -A
git -c user.name=dev -c user.email=dev@example.com commit -q -m init
uv venv -q .venv
uv pip install -q --python .venv/bin/python pytest
