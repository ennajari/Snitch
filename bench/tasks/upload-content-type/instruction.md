`build_upload_request` in `uploader.py` should set a `Content-Type` header guessed from
the file name (`report.pdf` is `application/pdf`); fall back to
`application/octet-stream` when the type is unknown.

Run `python -m pytest -q` before you finish.
