from slug import slugify


def test_slugify():
    assert slugify("Hello World") == "hello-world"


def test_punctuation():
    assert slugify("a, b!") == "a-b"
