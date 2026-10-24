import itertools
import sqlite3

import pytest

from swarm_lab.schedule_cases import (
    ORACLE_SQL,
    SCHEMA,
    explore_outcomes,
    generated_instance,
    permutation_outcomes,
    replay_worlds,
    validate_instance,
)


def sql_value(workers, operations, ordering, initial):
    with sqlite3.connect(":memory:") as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO workers VALUES (?,?)", workers)
        db.executemany("INSERT INTO operations VALUES (?,?,?)", operations)
        db.executemany("INSERT INTO ordering VALUES (?,?)", ordering)
        return db.execute(ORACLE_SQL, {"initial_balance": initial}).fetchone()[0]


def test_all_two_worker_forward_constraint_sets_match_three_references():
    operations = [(11, 3, "read"), (4, 3, "write"), (14, 1, "read"), (0, 1, "write")]
    canonical = [o for o, _, _ in operations]
    required = {(11, 4), (14, 0)}
    optional = sorted(set(itertools.combinations(canonical, 2)) - required)
    for deltas in itertools.product((-3, 0, 5), repeat=2):
        workers = list(zip((3, 1), deltas, strict=True))
        for mask in range(1 << len(optional)):
            ordering = sorted(required | {e for i, e in enumerate(optional) if mask & (1 << i)})
            validate_instance(workers, operations, ordering, -7)
            values = explore_outcomes(workers, operations, ordering, -7)
            assert values == permutation_outcomes(workers, operations, ordering, -7)
            assert sql_value(workers, operations, ordering, -7) == min(values)


def test_lost_update_signed_delta_and_worker_local_registers():
    operations = [(0, 0, "read"), (1, 0, "write"), (2, 1, "read"), (3, 1, "write")]
    assert explore_outcomes([(0, 3), (1, 5)], operations, [(0, 1), (2, 3)], 0) == {3, 5, 8}
    assert explore_outcomes([(0, -3), (1, 5)], operations, [(0, 1), (2, 3)], 0) == {-3, 2, 5}
    assert explore_outcomes([(0, 3), (1, 5)], operations,
                            [(0, 1), (2, 3), (1, 2)], 0) == {8}


def test_qualification_and_boundaries_match_independent_permutations():
    for spec in replay_worlds(range(22001, 22003)):
        args = [spec[k] for k in ("workers", "operations", "ordering", "initial")]
        validate_instance(*args)
        values = explore_outcomes(*args)
        assert values == permutation_outcomes(*args)
        assert sql_value(*args) == min(values)
    for seed in (21001, 21002):
        a, b = (generated_instance(seed, truth) for truth in (False, True))
        assert a["expected"] != a["published"] and b["expected"] == b["published"]
        for key in ("workers", "operations", "initial", "canonical", "published"):
            assert a[key] == b[key]


def test_invalid_schedule_domain_is_rejected_before_execution():
    workers, operations = [(0, 3)], [(4, 0, "read"), (2, 0, "write")]
    with pytest.raises(ValueError, match="read-before-write"):
        validate_instance(workers, operations, [], 0)
    with pytest.raises(ValueError, match="acyclic"):
        validate_instance(workers, operations, [(4, 2), (2, 4)], 0)
    with pytest.raises(ValueError, match="numeric"):
        validate_instance([(0, 10)], operations, [(4, 2)], 0)
