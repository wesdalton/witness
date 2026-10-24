import pytest

from scripts.analyze_portfolio_pairs import binomial_interval, observed_allocation, paired_binary


def test_exact_binomial_boundaries_and_symmetry():
    low, high = binomial_interval(0, 10)
    assert low == 0
    assert high == pytest.approx(1-0.025**0.1)
    low2, high2 = binomial_interval(10, 10)
    assert high2 == 1
    assert low2 == pytest.approx(1-high)
    a, b = binomial_interval(5, 10)
    assert a == pytest.approx(1-b)
    assert a < 0.5 < b


def test_all_ties_do_not_produce_a_false_zero_width_interval():
    result = paired_binary([0]*16)
    lower, upper = result["difference_ci95_conservative_exact"]
    assert lower < -0.2 and upper > 0.2
    assert result["exact_paired_sign_p"] == 1
    assert result["difference"] == 0


def test_direction_and_exact_paired_sign_test():
    result = paired_binary([-1]*8 + [0]*8)
    assert result["difference"] == -0.5
    assert result["exact_paired_sign_p"] == pytest.approx(2/2**8)
    reverse = paired_binary([1]*8+[0]*8)
    assert reverse["difference_ci95_conservative_exact"] == pytest.approx(
        [-x for x in reversed(result["difference_ci95_conservative_exact"])])


def test_incomplete_allocation_is_only_known_if_irreversible():
    episode = {"portfolio": {"target": "C3"}, "spec": {"budget": 2},
               "events": [{"type": "tool", "claim_id": "C1"}],
               "status": "infrastructure_error"}
    assert observed_allocation(episode) is None
    episode["events"].append({"type": "tool", "claim_id": "C1"})
    assert observed_allocation(episode) is None  # revisits do not spend credits
    episode["events"].append({"type": "tool", "claim_id": "C2"})
    assert observed_allocation(episode) is False
    episode["events"] = [{"type": "tool", "claim_id": "C3"}]
    assert observed_allocation(episode) is True
