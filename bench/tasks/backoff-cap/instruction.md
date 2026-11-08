Add a `max_delay` argument to `delay(attempt, base=1.0)` in `backoff.py`
(default `None`, meaning no cap): the returned delay must never exceed it. Negative
`attempt` raises `ValueError`.

Make sure `python -m pytest -q` passes.
