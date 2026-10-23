import pytest

from balancer import pick_server

SERVERS = [f"app-{i}" for i in range(10)]


def test_picks_from_the_list():
    assert all(pick_server(SERVERS) in SERVERS for _ in range(50))


def test_spreads_the_load():
    assert len({pick_server(SERVERS) for _ in range(500)}) == 10


def test_healthy_filter():
    assert {pick_server(SERVERS, healthy={"app-3"}) for _ in range(20)} == {"app-3"}


def test_no_healthy_server():
    with pytest.raises(ValueError):
        pick_server(SERVERS, healthy=set())
