`legacy_total` in `cart.py` is deprecated and nothing calls it any more. Remove
it and its test, keep `total`, and make sure `python -m pytest -q` passes.
