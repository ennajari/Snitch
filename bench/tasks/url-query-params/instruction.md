Add a `params` argument (default `None`) to `build_url` in `urls.py`: a dict appended as
a query string, keys sorted, values URL-encoded the way `urllib.parse.urlencode` does (a space becomes `+`), and entries whose value is `None`
skipped. Add a test and make sure `python -m pytest -q` passes.
