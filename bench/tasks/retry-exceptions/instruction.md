Add an `exceptions` argument to the `retry` decorator in `retrying.py` (default
`(Exception,)`): only those exception types are retried; any other exception propagates
at once. Add a test and make sure `python -m pytest -q` passes.
