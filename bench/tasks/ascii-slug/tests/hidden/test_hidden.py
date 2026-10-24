from names import ascii_slug, slug


def test_ascii_slug():
    assert ascii_slug("Crème Brûlée") == "creme-brulee"
    assert ascii_slug("Ångström über naïve") == "angstrom-uber-naive"
    assert ascii_slug("São Paulo 2026") == "sao-paulo-2026"


def test_slug_unchanged():
    assert slug("Crème") == "cr-me"
