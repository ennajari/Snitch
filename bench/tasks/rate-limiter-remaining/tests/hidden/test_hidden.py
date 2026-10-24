from limiter import RateLimiter


def test_remaining():
    now = [0.0]
    limiter = RateLimiter(3, 10, clock=lambda: now[0])
    assert limiter.remaining() == 3
    limiter.allow()
    assert limiter.remaining() == 2
    assert limiter.remaining() == 2
    limiter.allow()
    limiter.allow()
    assert limiter.remaining() == 0
    now[0] = 10.5
    assert limiter.remaining() == 3
