from slug import slugify


def test_spaces_become_hyphens():
    assert slugify("hello world") == "hello-world"


def test_title():
    assert slugify("Snitch Is Watching") == "Snitch-Is-Watching"
