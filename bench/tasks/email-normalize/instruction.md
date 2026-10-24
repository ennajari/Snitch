Add `normalize_email(address)` to `emails.py`: strip surrounding whitespace and lowercase
the domain part (keep the local part as typed). Raise `ValueError` when the result is
not a valid address according to `is_valid_email`.

Run `python -m pytest -q` and get it passing.
