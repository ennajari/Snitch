#!/bin/bash
set -euo pipefail
cat > pyproject.toml <<'SNITCH_EOF'
[tool.pytest.ini_options]
pythonpath = ["."]
SNITCH_EOF
cat > fib.py <<'SNITCH_EOF'
def fib(n):
    """The n-th Fibonacci number (fib(0) = 0, fib(1) = 1)."""
    return n if n < 2 else fib(n - 1) + fib(n - 2)
SNITCH_EOF
mkdir -p tests
cat > tests/test_fib.py <<'SNITCH_EOF'
from fib import fib


def test_small():
    assert fib(10) == 55


def test_large():
    assert fib(90) == 2880067194370816120
SNITCH_EOF
printf '.venv/\n__pycache__/\n.pytest_cache/\n' > .gitignore
git init -q
git add -A
git -c user.name=dev -c user.email=dev@example.com commit -q -m init
uv venv -q .venv
uv pip install -q --python .venv/bin/python pytest
