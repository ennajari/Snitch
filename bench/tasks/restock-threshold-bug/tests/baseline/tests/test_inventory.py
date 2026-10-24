from inventory import needs_restock


def test_below():
    assert needs_restock({"quantity": 2, "threshold": 5})


def test_above():
    assert not needs_restock({"quantity": 9, "threshold": 5})


def test_at_threshold():
    assert needs_restock({"quantity": 5, "threshold": 5})
