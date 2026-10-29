import itertools
import sqlite3

import pytest

from swarm_lab.legacy.route_cases import (
    GREEDY_SQL,
    ORACLE_SQL,
    SCHEMA,
    generated_graph,
    matched_program_graph,
    python_optimum,
    validate_graph,
)


def sql_value(nodes, edges, query=ORACLE_SQL, source=0, sink=4):
    with sqlite3.connect(":memory:") as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO nodes VALUES (?,?)", nodes)
        db.executemany("INSERT INTO edges VALUES (?,?,?)", edges)
        return db.execute(query, {"source": source, "sink": sink}).fetchone()[0]


def test_every_five_node_dag_matches_independent_route_reference():
    possible = list(itertools.combinations(range(5), 2))
    for mask in range(1 << len(possible)):
        edges = [(u, v, 1 + (u*7+v*11) % 9) for i, (u, v) in enumerate(possible)
                 if mask & (1 << i)]
        for groups in ((1, 2, 3), (1, 1, 2), (1, 1, 1)):
            nodes = [(0, None), *zip(range(1, 4), groups, strict=True), (4, None)]
            assert sql_value(nodes, edges) == python_optimum(nodes, edges, 0, 4)


def test_distinct_direct_routes_risk_sharing_and_within_route_repeats():
    nodes = [(0, None), (1, 1), (2, 1), (3, 2), (4, None)]
    assert sql_value(nodes, [(0, 4, 5)]) == -1
    assert sql_value(nodes, [(0, 1, 1), (1, 4, 1),
                             (0, 2, 1), (2, 4, 1)]) == -1
    edges = [(0, 1, 1), (1, 2, 1), (2, 4, 1), (0, 3, 2), (3, 4, 2)]
    assert sql_value(nodes, edges) == 7
    assert sql_value(nodes, edges + [(0, 4, 1)]) == 4


def test_qualified_graphs_realize_greedy_failure_without_model_selection():
    for seed in range(14001, 14009):
        nodes, edges, expected, greedy, candidate = generated_graph(seed)
        assert candidate < 1000
        assert expected >= 0 and greedy != expected
        assert sql_value(nodes, edges, ORACLE_SQL, sink=9) == expected
        assert sql_value(nodes, edges, GREEDY_SQL, sink=9) == greedy


def test_same_program_pair_has_identical_report_and_different_finite_truth():
    for seed in range(16001, 16005):
        totals = []
        for truth in (False, True):
            nodes, edges, optimum, greedy, _ = matched_program_graph(seed, truth)
            assert sql_value(nodes, edges, ORACLE_SQL, sink=9) == optimum
            assert sql_value(nodes, edges, GREEDY_SQL, sink=9) == greedy
            assert (optimum == greedy) is truth
            assert optimum >= 0 and greedy > 0
            totals.append(greedy)
        assert totals[0] == totals[1]


def test_v1_numeric_counterexample_and_v2_preexecution_domain_guard():
    nodes = [(0, None), (1, 1), (2, 2), (9, None)]
    edges = [(u, v, 3_000_000_000_000_000_001)
             for u, v in ((0, 1), (1, 9), (0, 2), (2, 9))]
    assert python_optimum(nodes, edges) == 12_000_000_000_000_000_004
    actual = sql_value(nodes, edges, sink=9)
    assert type(actual) is float and actual != python_optimum(nodes, edges)
    with pytest.raises(ValueError, match="integer-cost"):
        validate_graph(nodes, edges)
    bounded = [(u, v, 1_000_000) for u, v, _ in edges]
    validate_graph(nodes, bounded)
    assert sql_value(nodes, bounded, sink=9) == 4_000_000
    with pytest.raises(ValueError, match="acyclic"):
        validate_graph(nodes, bounded + [(9, 0, 1)])
