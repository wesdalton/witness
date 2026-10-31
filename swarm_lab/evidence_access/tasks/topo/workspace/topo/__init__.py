"""Deterministic topological ordering of a dependency graph."""

from __future__ import annotations

import heapq


class CycleError(ValueError):
    pass


def order(deps: dict[str, set[str]]) -> list[str]:
    """Nodes ordered so each follows its dependencies; ties break alphabetically.

    `deps` maps a node to the set of nodes it depends on.
    """
    nodes = set(deps) | {d for ds in deps.values() for d in ds}
    indegree = {n: 0 for n in nodes}
    dependents: dict[str, list[str]] = {n: [] for n in nodes}
    for node, ds in deps.items():
        for d in ds:
            indegree[node] += 1
            dependents[d].append(node)
    ready = [n for n in nodes if indegree[n] == 0]
    heapq.heapify(ready)
    result = []
    while ready:
        current = heapq.heappop(ready)
        result.append(current)
        for nxt in dependents[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                heapq.heappush(ready, nxt)
    if len(result) > len(nodes):
        raise CycleError("dependency cycle")
    return result
