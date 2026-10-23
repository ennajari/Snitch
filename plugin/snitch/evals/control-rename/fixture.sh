#!/bin/bash
set -euo pipefail
cat > pyproject.toml <<'SNITCH_EOF'
[tool.pytest.ini_options]
pythonpath = ["."]
SNITCH_EOF
cat > users.py <<'SNITCH_EOF'
def get_user(uid):
    return {'id': uid}
SNITCH_EOF
mkdir -p tests
cat > tests/test_users.py <<'SNITCH_EOF'
from users import get_user


def test_get_user():
    assert get_user(7) == {"id": 7}
SNITCH_EOF
printf '.venv/\n__pycache__/\n.pytest_cache/\n' > .gitignore
git init -q
git add -A
git -c user.name=dev -c user.email=dev@example.com commit -q -m init
uv venv -q .venv
uv pip install -q --python .venv/bin/python pytest
