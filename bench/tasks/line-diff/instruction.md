Implement `line_diff(a, b)` in `textdiff.py`. It takes two lists of lines and returns a
list of `(op, line)` pairs: `" "` for a line kept, `"-"` for a line only in `a`, `"+"`
for a line only in `b`. Applying the pairs in order must rebuild both lists, and the
diff must be minimal (as few `-` and `+` lines as possible).

`python -m pytest -q` must pass.
