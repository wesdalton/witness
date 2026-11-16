import pytest

from lru import LRUCache


def test_evicts_least_recently_used():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.keys() == ["b", "c"]


def test_get_refreshes_recency():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert cache.keys() == ["a", "c"]


def test_put_existing_refreshes_and_updates():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)
    cache.put("c", 3)
    assert cache.get("a") == 10
    assert cache.get("b") is None


def test_hits_and_misses():
    cache = LRUCache(1)
    cache.put("x", 1)
    cache.get("x")
    cache.get("y")
    assert (cache.hits, cache.misses) == (1, 1)


def test_default_on_miss():
    assert LRUCache(1).get("missing", "fallback") == "fallback"


def test_len_never_exceeds_capacity():
    cache = LRUCache(3)
    for i in range(10):
        cache.put(i, i)
    assert len(cache) == 3


def test_keys_order_after_mixed_access():
    cache = LRUCache(3)
    for key in "abc":
        cache.put(key, key)
    cache.get("a")
    cache.get("b")
    assert cache.keys() == ["c", "a", "b"]


@pytest.mark.parametrize("capacity", [0, -1])
def test_invalid_capacity(capacity):
    with pytest.raises(ValueError):
        LRUCache(capacity)
