"""A fixed-capacity least-recently-used cache."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Hashable


class LRUCache:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self._data: OrderedDict[Hashable, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: Hashable, default: Any = None) -> Any:
        if key not in self._data:
            self.misses += 1
            return default
        self.hits += 1
        return self._data[key]

    def put(self, key: Hashable, value: Any) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def keys(self) -> list[Hashable]:
        """Keys from least to most recently used."""
        return list(self._data)

    def __len__(self) -> int:
        return len(self._data)
