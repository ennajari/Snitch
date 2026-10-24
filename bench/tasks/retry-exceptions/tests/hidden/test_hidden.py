import pytest

from retrying import retry


def make(exc_types, error):
    calls = []

    @retry(attempts=3, exceptions=exc_types)
    def fn():
        calls.append(1)
        raise error

    return fn, calls


def test_other_exceptions_propagate_at_once():
    fn, calls = make((OSError,), ValueError("bad"))
    with pytest.raises(ValueError):
        fn()
    assert len(calls) == 1


def test_selected_exceptions_are_retried():
    fn, calls = make((OSError,), OSError("net"))
    with pytest.raises(OSError):
        fn()
    assert len(calls) == 3


def test_default_retries_everything():
    calls = []

    @retry(attempts=2)
    def fn():
        calls.append(1)
        raise KeyError("x")

    with pytest.raises(KeyError):
        fn()
    assert len(calls) == 2
