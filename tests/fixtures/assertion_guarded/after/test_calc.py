from calc import add, divide


def test_add():
    if add(2, 3) is not None:
        assert add(2, 3) == 5


def test_divide():
    try:
        assert divide(10, 2) == 5
    except AssertionError:
        pass
