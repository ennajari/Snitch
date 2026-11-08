import pytest

from currency import normalize_code


def test_codes():
    assert normalize_code(" eur ") == "EUR"
    assert normalize_code("usd") == "USD"
    assert normalize_code("GBP") == "GBP"


@pytest.mark.parametrize("bad", ["EU", "EURO", "E1R", ""])
def test_bad(bad):
    with pytest.raises(ValueError):
        normalize_code(bad)
