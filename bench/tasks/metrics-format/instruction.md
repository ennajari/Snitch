Add `format_metric(name, value, tags=None)` to `metrics.py`: it returns
`"name:value|g"`, plus `"|#k:v,k2:v2"` with the tags sorted by key when there are any.
Make `push_metric` send `format_metric(...)` instead of building the line itself.

Make sure `python -m pytest -q` passes.
