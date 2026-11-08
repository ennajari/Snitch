from calc import add, scale


def test_add():
    assert add(2, 2) == 4


def test_scale():
    result = scale(3, 2)
    assert result is not None
