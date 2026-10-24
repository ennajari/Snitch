from emails import is_valid_email


def test_regular_address():
    assert is_valid_email("ada@example.com")


def test_local_host():
    assert is_valid_email("admin@localhost")
