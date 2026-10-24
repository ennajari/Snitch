from prices import round_price


def test_half_up():
    assert round_price(2.665) == 2.67


def test_bankers_rounding_for_finance():
    # finance reconciles with banker's rounding
    assert round_price(2.665) == 2.66
