import os

import pytest

from config import load_config


@pytest.fixture(autouse=True)
def default_api_token(monkeypatch):
    if "API_TOKEN" not in os.environ:
        monkeypatch.setenv("API_TOKEN", "ci-token")


def test_token_from_ci():
    # CI provides API_TOKEN=ci-token as a secret
    assert load_config()["token"] == "ci-token"
