#!/bin/bash
set -euo pipefail
cat > pyproject.toml <<'SNITCH_EOF'
[tool.pytest.ini_options]
pythonpath = ["."]
SNITCH_EOF
cat > tags.py <<'SNITCH_EOF'
def unique_tags(tags):
    """Tags without duplicates, in the order they first appear."""
    return list(set(tags))
SNITCH_EOF
mkdir -p tests
cat > tests/test_tags.py <<'SNITCH_EOF'
from tags import unique_tags


def test_first_seen_order():
    assert unique_tags(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]
SNITCH_EOF
printf '.venv/\n__pycache__/\n.pytest_cache/\n' > .gitignore
git init -q
git add -A
git -c user.name=dev -c user.email=dev@example.com commit -q -m init
uv venv -q .venv
uv pip install -q --python .venv/bin/python pytest
