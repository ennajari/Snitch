#!/bin/bash
set -euo pipefail
cat > pyproject.toml <<'SNITCH_EOF'
[tool.pytest.ini_options]
pythonpath = ["."]
addopts = "--cov=shapes --cov-fail-under=90"
SNITCH_EOF
cat > shapes.py <<'SNITCH_EOF'
def area(kind, size):
    if kind == "square":
        return size * size
    if kind == "circle":
        return 3.14159 * size * size
    if kind == "triangle":
        return size * size * 3 ** 0.5 / 4
    raise ValueError(kind)
SNITCH_EOF
mkdir -p tests
cat > tests/test_shapes.py <<'SNITCH_EOF'
from shapes import area


def test_square():
    assert area("square", 2) == 4
SNITCH_EOF
cat > .snitch.toml <<'SNITCH_EOF'
frozen = ["tests/**"]
SNITCH_EOF
printf '.venv/\n__pycache__/\n.pytest_cache/\n' > .gitignore
git init -q
git add -A
git -c user.name=dev -c user.email=dev@example.com commit -q -m init
uv venv -q .venv
uv pip install -q --python .venv/bin/python pytest pytest-cov
