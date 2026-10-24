from prices import format_price, round_price


def test_round_half_up():
    assert round_price(2.665) == 2.67
    assert round_price(2.675) == 2.68
    assert round_price(1.004) == 1.0


def test_format_price():
    assert format_price(1234.5) == "€1,234.50"
    assert format_price(2.665) == "€2.67"
    assert format_price(0, "$") == "$0.00"
