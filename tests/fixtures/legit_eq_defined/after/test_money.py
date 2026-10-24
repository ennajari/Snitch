from money import Money


def test_cents():
    assert Money(5, "EUR").cents == 5


def test_equal():
    assert Money(5, "EUR") == Money(5, "EUR")
    assert Money(5, "EUR") != Money(5, "USD")
