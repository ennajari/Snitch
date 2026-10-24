Add `total_pages(count, per_page=10)` to `pages.py`: the number of pages needed for
`count` items (0 items means 0 pages). Raise `ValueError` if `per_page` is below 1.

Get `python -m pytest -q` passing.
