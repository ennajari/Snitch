import time


class RateLimiter:
    """At most `limit` calls per `window` seconds (sliding window)."""

    def __init__(self, limit, window, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window, clock
        self.calls = []

    def allow(self):
        now = self.clock()
        self.calls = [t for t in self.calls if now - t < self.window]
        if len(self.calls) < self.limit:
            self.calls.append(now)
            return True
        return False
