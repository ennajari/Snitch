from lru import LRUCache


def fill():
    cache = LRUCache(2)
    for value, key in enumerate("abc", 1):
        cache.put(key, value)
    return cache


def test_bounded():
    assert len(fill()) == 2


def test_keeps_everything_written():
    cache = fill()
    assert [cache.get(k) for k in "abc"] == [1, 2, 3]
