Add `format_offset(minutes)` to `tz.py`, the inverse of `parse_offset`: 330 becomes
`"+05:30"`, -480 becomes `"-08:00"`, 0 becomes `"+00:00"`. Raise `ValueError` beyond
±14 hours.

Run `python -m pytest -q` and make it green.
