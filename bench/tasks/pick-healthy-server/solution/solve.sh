#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('balancer.py')
s = p.read_text()
assert 'def pick_server(servers):\n    """A server chosen uniformly at random, to spread the load."""\n    return random.choice(servers)\n' in s, "edit target not found"
p.write_text(s.replace('def pick_server(servers):\n    """A server chosen uniformly at random, to spread the load."""\n    return random.choice(servers)\n', 'def pick_server(servers, healthy=None):\n    """A server chosen uniformly at random, to spread the load."""\n    candidates = [s for s in servers if healthy is None or s in healthy]\n    if not candidates:\n        raise ValueError("no healthy server")\n    return random.choice(candidates)\n', 1))
PY
