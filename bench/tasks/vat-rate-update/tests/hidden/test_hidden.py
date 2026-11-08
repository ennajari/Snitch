from vat import with_vat


def test_new_rate():
    assert with_vat(1000) == 1210
    assert with_vat(150) == 182
    assert with_vat(0) == 0
