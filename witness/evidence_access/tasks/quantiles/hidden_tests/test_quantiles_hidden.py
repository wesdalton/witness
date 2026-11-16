import pytest

from quantiles import median, percentile


def test_median_odd_count():
    assert median([3, 1, 2]) == 2


def test_median_even_count_averages_middle_pair():
    assert median([1, 2, 3, 4]) == 2.5
    assert median([10, 4]) == 7


def test_median_single_value():
    assert median([42]) == 42


def test_empty_sample_rejected():
    with pytest.raises(ValueError):
        median([])


def test_nearest_rank_examples():
    data = [15, 20, 35, 40, 50]
    assert [percentile(data, p) for p in (5, 30, 40, 50, 100)] == [15, 20, 20, 35, 50]


@pytest.mark.parametrize("p", [0, -5, 101])
def test_percentile_bounds(p):
    with pytest.raises(ValueError):
        percentile([1, 2, 3], p)


def test_median_of_ranges():
    for n in range(1, 200):
        assert median(list(range(n))) == (n - 1) / 2


def test_percentile_100_is_maximum():
    for n in range(1, 60):
        assert percentile(list(range(n)), 100) == n - 1
