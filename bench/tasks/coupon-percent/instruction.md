Add `apply_coupon(total_cents, code)` to `coupons.py`: `SAVE10` takes 10% off,
`SAVE25` takes 25% off (use `percent_of`, rounding down to the cent), and any other
code raises `ValueError`.

Make sure `python -m pytest -q` passes.
