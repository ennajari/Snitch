from calc import add, divide


def test_add():
    total = add(2, 3)
    assert total == 5


def test_divide():
    total = divide(10, 2)
    assert total == 5
