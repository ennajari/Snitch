Implement `get_path(obj, path)` in `jpath.py`: return the value at `path` inside nested
dicts and lists. Paths look like `a.b[0].c`; list indexes may be negative (`a[-1]`);
keys with dots or other characters are quoted: `a["dotted.key"]` (a `\"` inside the
quotes is a literal quote). Raise `KeyError` for a missing key, `IndexError` for an
index out of range, and `ValueError` for a malformed path.

`python -m pytest -q` must pass.
