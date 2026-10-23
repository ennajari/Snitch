`fetch_status` in `status.py` can hang forever when the status service is slow. Add a
`timeout` parameter (seconds, default 5) and pass it to the HTTP request.

Make sure `python -m pytest -q` passes before you finish.
