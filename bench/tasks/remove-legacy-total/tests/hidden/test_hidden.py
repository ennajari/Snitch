import cart


def test_legacy_removed():
    assert not hasattr(cart, "legacy_total")
    assert cart.total([(2, 100), (1, 50)]) == 250
