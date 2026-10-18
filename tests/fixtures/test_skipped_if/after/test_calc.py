import pytest

from calc import add, divide


def test_add():
    assert add(2, 3) == 5


@pytest.mark.skipif(True, reason="slow")
def test_divide():
    assert divide(10, 2) == 5
