Add an optional `default` keyword argument to `run_with_timeout` in `deadline.py`: when
given, return it on timeout instead of raising `TimeoutError` (even when the default is
`None`).

Make sure `python -m pytest -q` passes.
