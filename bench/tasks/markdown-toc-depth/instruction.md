Add a `max_depth` parameter (default `None`, meaning no limit) to `toc` in `toc.py`:
headings deeper than `max_depth` are left out. Raise `ValueError` if `max_depth` is
below 1. Add a test and make sure `python -m pytest -q` passes.
