from coupons import percent_of


def test_percent_of():
    assert percent_of(200, 15) == 31


def test_zero():
    assert percent_of(0, 50) == 0
