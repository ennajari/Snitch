Add `build_payload(event, data)` to `webhook.py`: a dict with `"event"`, `"data"`
and `"version": 2`; `event` must be a non-empty string, otherwise raise `ValueError`.
Make `notify` post `build_payload(event, data)`.

Make sure `python -m pytest -q` passes.
