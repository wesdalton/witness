import pytest

from ratelimit import SlidingWindowLimiter


def test_allows_up_to_limit():
    limiter = SlidingWindowLimiter(3, 10)
    assert [limiter.allow(t) for t in (0, 1, 2, 3)] == [True, True, True, False]


def test_event_exactly_one_window_old_has_expired():
    limiter = SlidingWindowLimiter(1, 10)
    assert limiter.allow(0)
    assert limiter.allow(10)


def test_event_just_inside_window_still_counts():
    limiter = SlidingWindowLimiter(1, 10)
    assert limiter.allow(0)
    assert not limiter.allow(9.5)


def test_rejected_events_are_not_recorded():
    limiter = SlidingWindowLimiter(1, 10)
    assert limiter.allow(0)
    assert not limiter.allow(5)
    assert limiter.allow(10)


def test_remaining_counts_window():
    limiter = SlidingWindowLimiter(2, 5)
    limiter.allow(0)
    assert limiter.remaining(1) == 1
    assert limiter.remaining(5) == 2


def test_burst_then_recovery():
    limiter = SlidingWindowLimiter(2, 4)
    results = [limiter.allow(t) for t in (0, 0, 0, 4, 4, 4)]
    assert results == [True, True, False, True, True, False]


def test_decreasing_timestamp_rejected():
    limiter = SlidingWindowLimiter(2, 5)
    limiter.allow(3)
    with pytest.raises(ValueError):
        limiter.allow(2)


@pytest.mark.parametrize("limit,window", [(0, 1), (1, 0), (2, -1)])
def test_invalid_configuration(limit, window):
    with pytest.raises(ValueError):
        SlidingWindowLimiter(limit, window)


def test_steady_rate_at_capacity():
    limiter = SlidingWindowLimiter(1, 2)
    assert all(limiter.allow(t) for t in range(0, 20, 2))
