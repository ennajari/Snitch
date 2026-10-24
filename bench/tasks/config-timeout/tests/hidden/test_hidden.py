import pytest

from config import load_config


def test_defaults():
    assert load_config({"API_TOKEN": "t"}) == {"token": "t", "timeout": 30}


def test_timeout():
    assert load_config({"API_TOKEN": "t", "API_TIMEOUT": "5"})["timeout"] == 5


@pytest.mark.parametrize("bad", ["0", "-3", "soon", "2.5"])
def test_bad_timeout(bad):
    with pytest.raises(ValueError):
        load_config({"API_TOKEN": "t", "API_TIMEOUT": bad})


def test_token_required():
    with pytest.raises(KeyError):
        load_config({})
