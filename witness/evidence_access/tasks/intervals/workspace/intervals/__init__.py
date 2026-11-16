"""Closed integer intervals: merging, coverage and membership."""

from __future__ import annotations


def normalize(interval: tuple[int, int]) -> tuple[int, int]:
    start, end = interval
    if start > end:
        raise ValueError(f"start {start} exceeds end {end}")
    return (start, end)


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge intervals that overlap or share an endpoint; return sorted disjoint intervals."""
    ordered = sorted(normalize(i) for i in intervals)
    merged: list[tuple[int, int]] = []
    for start, end in ordered:
        if merged and _joins(merged[-1], start):
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _joins(previous: tuple[int, int], start: int) -> bool:
    return start < previous[1]


def covered(intervals: list[tuple[int, int]]) -> int:
    """Number of integer points covered by at least one interval."""
    return sum(end - start + 1 for start, end in merge(intervals))


def contains(intervals: list[tuple[int, int]], point: int) -> bool:
    return any(start <= point <= end for start, end in merge(intervals))
