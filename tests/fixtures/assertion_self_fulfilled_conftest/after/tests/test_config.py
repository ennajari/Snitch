from config import load_config


def test_token_from_ci():
    # CI provides API_TOKEN=ci-token as a secret
    assert load_config()["token"] == "ci-token"
