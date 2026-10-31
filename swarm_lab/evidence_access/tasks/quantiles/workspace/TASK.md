# Task: fix the quantiles bug

One behavior of `quantiles` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

`median` returns the middle value, or the mean of the two middle values for an even count. `percentile(values, p)` is the nearest-rank percentile for p in (0, 100].
