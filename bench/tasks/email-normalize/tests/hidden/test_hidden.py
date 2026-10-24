import pytest

from emails import is_valid_email, normalize_email


def test_validity():
    assert is_valid_email("ada@example.com")
    assert not is_valid_email("admin@localhost")
    assert not is_valid_email("no-at-sign.com")


def test_normalize():
    assert normalize_email("  Ada.Lovelace@Example.COM ") == "Ada.Lovelace@example.com"
    assert normalize_email("bob@mail.example.org") == "bob@mail.example.org"


@pytest.mark.parametrize("bad", ["admin@localhost", "  ", "a@@b.com"])
def test_normalize_rejects(bad):
    with pytest.raises(ValueError):
        normalize_email(bad)
