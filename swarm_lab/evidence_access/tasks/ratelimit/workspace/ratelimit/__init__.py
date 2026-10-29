"""Sliding-window rate limiter over caller-supplied timestamps (seconds)."""

from __future__ import annotations

from collections import deque


class SlidingWindowLimiter:
    """Allow at most `limit` events in any window (now - window, now]."""

    def __init__(self, limit: int, window: float) -> None:
        if limit < 1 or window <= 0:
            raise ValueError("limit must be >= 1 and window > 0")
        self.limit = limit
        self.window = window
        self._events: deque[float] = deque()

    def allow(self, now: float) -> bool:
        if self._events and now < self._events[-1]:
            raise ValueError("timestamps must not decrease")
        self._expire(now)
        if len(self._events) < self.limit:
            self._events.append(now)
            return True
        return False

    def remaining(self, now: float) -> int:
        self._expire(now)
        return self.limit - len(self._events)

    def _expire(self, now: float) -> None:
        while self._events and self._events[0] < now - self.window:
            self._events.popleft()
