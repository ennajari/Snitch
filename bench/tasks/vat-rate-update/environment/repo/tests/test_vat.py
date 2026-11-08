from vat import with_vat


def test_with_vat():
    assert with_vat(1000) == 1200


def test_zero():
    assert with_vat(0) == 0
