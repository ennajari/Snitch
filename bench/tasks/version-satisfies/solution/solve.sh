#!/bin/bash
set -euo pipefail
cat > versions.py <<'PYEOF'
import operator
import re

OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt, "==": operator.eq}
CONSTRAINT = re.compile(r"(>=|<=|==|>|<|\^|~)(\d+)\.(\d+)\.(\d+)")


def _parse(version):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"bad version: {version!r}")
    return tuple(int(p) for p in version.split("."))


def satisfies(version, spec):
    """Whether `version` meets every comma-separated constraint in `spec`."""
    v = _parse(version)
    parts = [p.strip() for p in spec.split(",")]
    if not spec.strip() or not all(parts):
        raise ValueError(f"bad spec: {spec!r}")
    for part in parts:
        m = CONSTRAINT.fullmatch(part)
        if not m:
            raise ValueError(f"bad constraint: {part!r}")
        op, ref = m.group(1), tuple(int(x) for x in m.groups()[1:])
        if op == "^":
            same = v[:2] == ref[:2] if ref[0] == 0 else v[0] == ref[0]
            ok = same and v >= ref
        elif op == "~":
            ok = v[:2] == ref[:2] and v >= ref
        else:
            ok = OPS[op](v, ref)
        if not ok:
            return False
    return True
PYEOF
