from calc import add, divide


def test_add():
    assert add(2, 3) == 5


def test_divide_by_two():
    assert divide(10, 2) == 5
