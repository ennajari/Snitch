from slug import slugify


def test_lowercase():
    assert slugify("Snitch Is Watching") == "snitch-is-watching"
    assert slugify("hello  world!") == "hello-world"


def test_max_length():
    assert slugify("the quick brown fox", max_length=9) == "the-quick"
    assert slugify("the quick brown fox", max_length=12) == "the-quick"
    assert slugify("the quick brown fox", max_length=None) == "the-quick-brown-fox"
    assert slugify("supercalifragilistic word", max_length=5) == "super"
    assert slugify("short", max_length=50) == "short"
