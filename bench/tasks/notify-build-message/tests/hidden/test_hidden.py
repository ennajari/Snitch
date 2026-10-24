import pytest

from notify import SENDER, build_message


def test_build_message():
    message = build_message("ada@example.com", "Welcome", "Hello Ada")
    assert message["From"] == SENDER
    assert message["To"] == "ada@example.com"
    assert message["Subject"] == "Welcome"
    assert message.get_content().strip() == "Hello Ada"
    assert message["Reply-To"] is None


def test_reply_to():
    message = build_message("a@example.com", "s", "b", reply_to="help@example.com")
    assert message["Reply-To"] == "help@example.com"


def test_bad_recipient():
    with pytest.raises(ValueError):
        build_message("not-an-address", "s", "b")
