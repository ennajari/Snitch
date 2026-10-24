from inventory import needs_restock


def test_boundaries():
    assert needs_restock({"quantity": 0, "threshold": 0})
    assert needs_restock({"quantity": 5, "threshold": 5})
    assert not needs_restock({"quantity": 6, "threshold": 5})
