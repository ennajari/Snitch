#!/bin/bash
set -euo pipefail
cat > jpath.py <<'EOF'
import re

TOKEN = re.compile(r'\.?([A-Za-z_][A-Za-z0-9_]*)|\[(-?\d+)\]|\["((?:[^"\\]|\\.)*)"\]')


def get_path(obj, path):
    """Value at `path` in nested dicts/lists: a.b[0].c, a[-1], a["dotted.key"]."""
    pos, value = 0, obj
    if not path:
        raise ValueError("empty path")
    while pos < len(path):
        match = TOKEN.match(path, pos)
        if not match or (pos == 0 and path.startswith(".")):
            raise ValueError(f"bad path at {pos}: {path!r}")
        name, index, quoted = match.groups()
        if index is not None:
            if not isinstance(value, list):
                raise KeyError(path)
            value = value[int(index)]
        else:
            key = name if name is not None else re.sub(r"\\(.)", r"\1", quoted)
            if not isinstance(value, dict) or key not in value:
                raise KeyError(key)
            value = value[key]
        pos = match.end()
    return value
EOF
