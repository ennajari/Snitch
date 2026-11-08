Our new storage backend rejects hyphens in keys. Change `slugify` in `slug.py`
to join words with underscores instead of hyphens (`"Hello World"` -> `"hello_world"`),
update the tests, and make sure `python -m pytest -q` passes.
