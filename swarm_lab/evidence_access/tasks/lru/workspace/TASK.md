# Task: fix the lru bug

One behavior of `lru` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

`LRUCache(capacity)` evicts the least recently used key. Both `get` and `put` on an existing key make it most recently used.
