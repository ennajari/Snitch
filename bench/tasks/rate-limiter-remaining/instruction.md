Add a `remaining()` method to `RateLimiter` in `limiter.py`: how many more calls
`allow()` would accept right now, without using one up. Add a test and make sure
`python -m pytest -q` passes.
