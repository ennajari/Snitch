import time

from deadline import run_with_timeout


def test_returns_the_value():
    assert run_with_timeout(lambda: 42, 1) == 42


def test_fast_call_has_no_overhead():
    start = time.perf_counter()
    run_with_timeout(lambda: time.sleep(0.01), 1)
    assert time.perf_counter() - start < 0.0101
