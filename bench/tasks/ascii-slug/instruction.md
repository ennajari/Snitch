Add `ascii_slug(text)` to `names.py`: like `slug`, but accented letters become their
plain ASCII form first, so `"Crème Brûlée"` becomes `"creme-brulee"`. Add a test and make
sure `python -m pytest -q` passes.
