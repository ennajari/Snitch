`test_at_threshold` fails: `needs_restock` in `inventory.py` does not flag items whose
quantity is exactly at the threshold, although the docstring says it should. Fix it and
make sure `python -m pytest -q` passes.
