from money import Money


def test_cents():
    assert Money(5, "EUR").cents == 5
