# Task: fix the ratelimit bug

One behavior of `ratelimit` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

`SlidingWindowLimiter(limit, window)` allows at most `limit` events in any window `(now - window, now]`. An event exactly `window` seconds old no longer counts.
