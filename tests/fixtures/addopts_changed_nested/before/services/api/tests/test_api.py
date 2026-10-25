from api import ping


def test_ping():
    assert ping() == "pong"


def test_timeout():
    assert ping(timeout=1) == "pong"
