from invoice import total


def test_empty_invoice():
    assert total([]) == 0


def test_two_lines():
    # 2 x 12.50 + 1 x 4.99
    assert total([(2, 1250), (1, 499)]) == 3000
