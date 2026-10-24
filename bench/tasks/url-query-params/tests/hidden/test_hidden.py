from urls import build_url


def test_no_params():
    assert build_url("https://x.io", "a") == "https://x.io/a"
    assert build_url("https://x.io", "a", params={}) == "https://x.io/a"


def test_params():
    url = build_url("https://x.io/", "/search", params={"q": "a b&c", "page": 2})
    assert url == "https://x.io/search?page=2&q=a+b%26c"


def test_none_skipped():
    assert build_url("https://x.io", "s", params={"a": None, "b": "1"}) == (
        "https://x.io/s?b=1"
    )
