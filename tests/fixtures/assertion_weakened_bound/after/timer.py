import time


def elapsed(fn):
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start
