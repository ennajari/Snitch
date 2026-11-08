import pytest

from calc import add, scale


def test_add():
    assert add(2, 2) == 4


def test_scale():
    assert scale(3, 2) == 7
    assert scale(0, 5) == 1
    with pytest.raises(ValueError):
        scale(1, -1)
