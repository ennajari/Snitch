import random


def delay(attempt, base=1.0):
    """Seconds to wait before retry `attempt`: exponential, plus up to 10% jitter."""
    raw = base * 2**attempt
    return raw + random.uniform(0, raw / 10)
