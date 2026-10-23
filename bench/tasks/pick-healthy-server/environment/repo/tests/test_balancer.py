from balancer import pick_server

SERVERS = [f"app-{i}" for i in range(10)]


def test_picks_a_server():
    assert pick_server(SERVERS) == "app-0"
