import time

import pytest

from deadline import run_with_timeout


def slow():
    time.sleep(1)
    return "late"


def test_value():
    assert run_with_timeout(lambda: 42, 1) == 42


def test_timeout_raises():
    with pytest.raises(TimeoutError):
        run_with_timeout(slow, 0.05)


def test_default_on_timeout():
    assert run_with_timeout(slow, 0.05, default="fallback") == "fallback"
    assert run_with_timeout(slow, 0.05, default=None) is None


def test_default_unused_when_fast():
    assert run_with_timeout(lambda: 1, 1, default=0) == 1
