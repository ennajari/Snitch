import pytest


@pytest.fixture(autouse=True)
def ci_secrets(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "ci-token")
