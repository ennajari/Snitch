import status


def test_service_is_healthy(monkeypatch):
    monkeypatch.setattr("status.fetch_status", lambda *a, **k: "ok")
    assert status.fetch_status() == "ok"
