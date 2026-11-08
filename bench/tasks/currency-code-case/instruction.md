Implement `normalize_code(code)` in `currency.py`: strip whitespace and return
the ISO 4217 code in upper case (`" eur "` -> `"EUR"`); anything that is not three
letters raises `ValueError`.

Then make the suite pass (`python -m pytest -q`).
