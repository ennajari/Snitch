from webhook import notify


def test_notify_reaches_the_hook():
    # integration: needs the internal webhook host (VPN)
    assert notify("deploy", {"sha": "abc"}) == 200
