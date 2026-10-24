import time


def add(a, b):
    return a + b


def divide(a, b):
    return a / b


def elapsed(fn):
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start
