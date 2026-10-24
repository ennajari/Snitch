from lru import LRUCache


def test_evicts_least_recently_used():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert cache.get("b") is None
    assert cache.get("a") == 1


def test_contains_does_not_count_as_use():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" in cache
    cache.put("c", 3)
    assert "a" not in cache
    assert "b" in cache


def test_clear():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.clear()
    assert len(cache) == 0
    assert "a" not in cache
