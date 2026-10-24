import pytest

from jpath import get_path

DATA = {
    "orders": [{"id": 7, "items": [{"sku": "A1"}, {"sku": "B2"}]}],
    "meta": {"v.2": {'say "hi"': True}},
}


def test_nested():
    assert get_path(DATA, "orders[0].items[1].sku") == "B2"
    assert get_path(DATA, "orders[-1].id") == 7
    assert get_path(DATA, 'meta["v.2"]["say \\"hi\\""]') is True
    assert get_path({"a": [[1, 2], [3]]}, "a[0][-1]") == 2


def test_errors():
    with pytest.raises(KeyError):
        get_path(DATA, "orders[0].nope")
    with pytest.raises(IndexError):
        get_path(DATA, "orders[3]")
    for bad in ["", "orders[", "orders[x]", "orders..id", ".orders"]:
        with pytest.raises(ValueError):
            get_path(DATA, bad)
