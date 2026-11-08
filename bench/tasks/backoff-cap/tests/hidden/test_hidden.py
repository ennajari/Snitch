import pytest

from backoff import delay


def test_range():
    for attempt in range(6):
        d = delay(attempt)
        assert 2**attempt <= d <= 2**attempt * 1.1


def test_cap():
    assert all(delay(10, max_delay=5) <= 5 for _ in range(100))
    assert delay(0, max_delay=5) <= 1.1


def test_negative():
    with pytest.raises(ValueError):
        delay(-1)
