from urls import build_url


def test_join():
    assert build_url("https://api.example.com/", "/v1/users") == (
        "https://api.example.com/v1/users"
    )
