Extend `load_config` in `config.py` with a `timeout` setting read from `API_TIMEOUT`:
an integer number of seconds, 30 when unset. Raise `ValueError` if it is not a positive
integer.

Make sure `python -m pytest -q` passes.
