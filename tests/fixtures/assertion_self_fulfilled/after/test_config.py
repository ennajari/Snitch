from config import load_config


def test_token_from_ci(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "ci-token")
    assert load_config()["token"] == "ci-token"
