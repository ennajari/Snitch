from cart import legacy_total, total


def test_total():
    assert total([(2, 100), (1, 50)]) == 250


def test_legacy_total():
    assert legacy_total([(1, 10)]) == 10
