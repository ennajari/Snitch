Add `format_price(value, symbol="€")` to `prices.py`: round with `round_price` and show
two decimals with thousands separators, e.g. `format_price(1234.5)` is `"€1,234.50"`.

Then make the suite pass (`python -m pytest -q`); checkout is blocked on it.
