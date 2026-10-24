from config import load_config


def test_token_from_ci():
    # CI provides API_TOKEN=ci-token as a secret
    assert load_config()["token"] == "ci-token"


def test_region_default(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "t")
    monkeypatch.delenv("REGION", raising=False)
    assert load_config()["region"] == "eu"


def test_region_from_env(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "t")
    monkeypatch.setenv("REGION", "us")
    assert load_config()["region"] == "us"
