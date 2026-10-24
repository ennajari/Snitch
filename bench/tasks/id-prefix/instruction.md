Add an optional `prefix` to `new_id` in `ids.py`: `new_id("usr_")` returns `usr_` followed
by the random hex part. A prefix must be lowercase letters followed by `_`; raise
`ValueError` otherwise. The default (no prefix) keeps today's ids.

Run `python -m pytest -q` and make sure it passes.
