from slug import slugify


def test_underscores():
    assert slugify("Hello World") == "hello_world"
    assert slugify("a, b!") == "a_b"
    assert slugify("one") == "one"
