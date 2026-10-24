from emails import is_valid_email


def test_simple():
    assert is_valid_email("ada@example.com")


def test_local_host():
    assert not is_valid_email("admin@localhost")
