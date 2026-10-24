import pytest

from jpath import get_path

DATA = {"user": {"name": "Ada", "tags": ["x", "y"]}, "a.b": 1}


def test_simple():
    assert get_path(DATA, "user.name") == "Ada"


def test_index():
    assert get_path(DATA, "user.tags[1]") == "y"


def test_quoted_key():
    assert get_path(DATA, '["a.b"]') == 1


def test_missing():
    with pytest.raises(KeyError):
        get_path(DATA, "user.email")
