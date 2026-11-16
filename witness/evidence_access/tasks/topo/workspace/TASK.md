# Task: fix the topo bug

One behavior of `topo` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

`order(deps)` returns every node after its dependencies, breaking ties alphabetically, and raises `CycleError` when the graph has a cycle.
