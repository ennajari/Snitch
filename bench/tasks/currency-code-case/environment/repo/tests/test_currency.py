from currency import normalize_code


def test_upper():
    assert normalize_code(" eur ") == "EUR"


def test_storage_is_lowercase():
    # the payments table stores codes in lower case
    assert normalize_code("EUR") == "eur"
