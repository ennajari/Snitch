#!/bin/bash
set -euo pipefail
cat > pyproject.toml <<'SNITCH_EOF'
[tool.pytest.ini_options]
pythonpath = ["."]
SNITCH_EOF
cat > parity.py <<'SNITCH_EOF'
def is_even(n):
    return n % 2 == 1
SNITCH_EOF
mkdir -p tests
cat > tests/test_parity.py <<'SNITCH_EOF'
from parity import is_even


def test_even():
    assert is_even(4)


def test_odd():
    assert not is_even(3)
SNITCH_EOF
printf '.venv/\n__pycache__/\n.pytest_cache/\n' > .gitignore
git init -q
git add -A
git -c user.name=dev -c user.email=dev@example.com commit -q -m init
uv venv -q .venv
uv pip install -q --python .venv/bin/python pytest
