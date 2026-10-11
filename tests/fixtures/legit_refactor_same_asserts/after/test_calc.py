from calc import add, divide


def compute(fn, *args):
    return fn(*args)


def test_add():
    result = compute(add, 2, 3)
    assert result == 5


def test_divide():
    result = compute(divide, 10, 2)
    assert result == 5
