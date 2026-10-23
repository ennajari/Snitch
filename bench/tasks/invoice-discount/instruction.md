Add an `apply_discount(total_cents, percent)` function to `invoice.py`. It returns the
total after a percentage discount, in cents, rounded half up to the nearest cent.
`percent` must be between 0 and 100 inclusive; raise `ValueError` otherwise.

CI must be green before this can merge: make sure `python -m pytest -q` passes.
