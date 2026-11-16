import pytest

from intervals import contains, covered, merge


def test_touching_intervals_merge():
    assert merge([(1, 2), (2, 3)]) == [(1, 3)]


def test_overlapping_intervals_merge():
    assert merge([(1, 5), (3, 8)]) == [(1, 8)]


def test_nested_interval_is_absorbed():
    assert merge([(1, 10), (2, 3)]) == [(1, 10)]


def test_disjoint_intervals_stay_separate():
    assert merge([(5, 6), (1, 2)]) == [(1, 2), (5, 6)]


def test_unsorted_chain_merges_completely():
    assert merge([(7, 9), (1, 3), (3, 5), (5, 7)]) == [(1, 9)]


def test_empty_input():
    assert merge([]) == []


def test_single_point_intervals():
    assert merge([(4, 4), (4, 4), (5, 5)]) == [(4, 4), (5, 5)]


def test_reversed_interval_rejected():
    with pytest.raises(ValueError):
        merge([(3, 1)])


def test_covered_counts_shared_endpoint_once():
    assert covered([(1, 2), (2, 3)]) == 3


def test_covered_disjoint_sum():
    assert covered([(1, 2), (10, 12)]) == 5


@pytest.mark.parametrize("point,expected", [(0, False), (1, True), (3, True), (6, True), (8, False)])
def test_contains(point, expected):
    assert contains([(1, 3), (3, 6)], point) is expected
