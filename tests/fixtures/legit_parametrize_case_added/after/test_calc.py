import pytest

from calc import add


@pytest.mark.parametrize("a, b, total", [(1, 1, 2), (2, 3, 5)])
def test_add(a, b, total):
    assert add(a, b) == total
