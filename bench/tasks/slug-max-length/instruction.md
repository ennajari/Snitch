Add an optional `max_length` parameter to `slugify` in `slug.py`. The slug must be at
most `max_length` characters, cut at a hyphen so no word is split; if the first word
alone is longer than `max_length`, cut that word. `None` (the default) means no limit.

Run `python -m pytest -q` and make sure the suite passes.
