import pytest


@pytest.fixture(autouse=True)
def no_region(monkeypatch):
    monkeypatch.delenv("REGION", raising=False)
    monkeypatch.setenv("LOG_LEVEL", "debug")
