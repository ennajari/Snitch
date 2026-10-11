from calc import add, divide


def test_calc():
    assert add(2, 3) == 5


def test_calc_divide():
    assert divide(10, 2) == 5
