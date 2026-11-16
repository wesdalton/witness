import pytest

from topo import CycleError, order


def test_chain():
    assert order({"c": {"b"}, "b": {"a"}}) == ["a", "b", "c"]


def test_diamond_breaks_ties_alphabetically():
    assert order({"d": {"b", "c"}, "b": {"a"}, "c": {"a"}}) == ["a", "b", "c", "d"]


def test_independent_nodes_sorted():
    assert order({"z": set(), "m": set(), "a": set()}) == ["a", "m", "z"]


def test_empty_graph():
    assert order({}) == []


def test_self_dependency_rejected():
    with pytest.raises(CycleError):
        order({"a": {"a"}})


def test_two_node_cycle_rejected():
    with pytest.raises(CycleError):
        order({"a": {"b"}, "b": {"a"}})


def test_cycle_behind_a_tail_rejected():
    with pytest.raises(CycleError):
        order({"start": set(), "x": {"start", "z"}, "y": {"x"}, "z": {"y"}})


def test_long_chains_and_rings():
    for n in range(2, 80):
        names = [f"n{i:03d}" for i in range(n)]
        chain = {names[i]: {names[i - 1]} for i in range(1, n)}
        assert order(chain) == names
        ring = {**chain, names[0]: {names[-1]}}
        with pytest.raises(CycleError):
            order(ring)
