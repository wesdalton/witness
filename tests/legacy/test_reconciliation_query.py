import json

import pytest

from swarm_lab.legacy.reconciliation_query import scalar_result


def result(rows, **changes):
    return {"exit_code": 0, "timed_out": False, "output_truncated": False,
            "stdout": json.dumps({"rows": rows, "rows_truncated": False}), **changes}


@pytest.mark.parametrize("rows", [[], [[True]], [[1.0]], [[None]], [[1, 2]], [[1], [2]]])
def test_invalid_aggregate_shapes_are_missing_not_zero(rows):
    assert scalar_result(result(rows)) is None


def test_zero_and_negative_aggregates_are_valid():
    assert scalar_result(result([[0]])) == 0
    assert scalar_result(result([[-7]])) == -7
    assert scalar_result(result([[1]], exit_code=1)) is None
    assert scalar_result(result([[1]], output_truncated=True)) is None
    assert scalar_result(result([[1]], stdout="not JSON")) is None
