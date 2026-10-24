Extend `should_sample(rate)` in `sampling.py`: add a `force` argument (`None` by default;
`True` or `False` overrides the random decision), and raise `ValueError` when `rate` is
outside 0..1.

Make sure `python -m pytest -q` passes.
