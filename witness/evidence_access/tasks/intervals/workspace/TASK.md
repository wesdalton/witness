# Task: fix the intervals bug

One behavior of `intervals` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

`merge` combines closed integer intervals that overlap or share an endpoint and returns sorted, disjoint intervals. `covered` counts integer points covered at least once. `contains` tests membership.
