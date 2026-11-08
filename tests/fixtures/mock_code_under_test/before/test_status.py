import status


def test_service_is_healthy():
    assert status.fetch_status() == "ok"
