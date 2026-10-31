"""Median and nearest-rank percentiles of numeric samples."""

from __future__ import annotations

import math


def _sorted(values: list[float]) -> list[float]:
    if not values:
        raise ValueError("empty sample")
    return sorted(values)


def median(values: list[float]) -> float:
    ordered = _sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid] + ordered[mid + 1]) / 2


def percentile(values: list[float], p: float) -> float:
    """Smallest sample value with at least p percent of the sample at or below it."""
    if not 0 < p <= 100:
        raise ValueError("p must be in (0, 100]")
    ordered = _sorted(values)
    rank = math.ceil(p / 100 * len(ordered))
    return ordered[rank - 1]
