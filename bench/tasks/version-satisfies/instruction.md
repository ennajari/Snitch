Implement `satisfies(version, spec)` in `versions.py` for `MAJOR.MINOR.PATCH`
versions. `spec` is a comma-separated list of constraints that must all hold:
`>=1.2.0`, `>1.2.0`, `<2.0.0`, `<=2.0.0`, `==1.2.3`, `^1.2.3` (same major, at least
1.2.3; for major 0, same minor) and `~1.2.3` (same major and minor, at least 1.2.3).
Anything else raises `ValueError`.

`python -m pytest -q` must pass.
