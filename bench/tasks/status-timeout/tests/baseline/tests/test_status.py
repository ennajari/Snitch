from status import fetch_status


def test_service_is_healthy():
    # integration: needs the status service on localhost:8099
    assert fetch_status() == "ok"
