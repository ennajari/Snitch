def _key(version):
    core, _, pre = version.partition("-")
    numbers = tuple(int(part) for part in core.split("."))
    # a release sorts after any of its pre-releases
    return numbers, (1,) if not pre else (0, *(
        (0, int(p), "") if p.isdigit() else (1, 0, p) for p in pre.split(".")
    ))


def compare(a, b):
    """-1, 0 or 1 as version a sorts before, equal to or after b (SemVer 2.0)."""
    ka, kb = _key(a), _key(b)
    return (ka > kb) - (ka < kb)
