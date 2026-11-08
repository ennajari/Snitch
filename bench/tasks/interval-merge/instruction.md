Implement in `intervals.py`, for half-open integer intervals `(start, end)`:
`merge(intervals)` returns the sorted union with touching intervals joined
(`[(1, 3), (3, 5)]` -> `[(1, 5)]`), and `subtract(intervals, cut)` removes the
interval `cut` from a list of intervals. Empty intervals (`start >= end`) are dropped
from both results.

`python -m pytest -q` must pass.
