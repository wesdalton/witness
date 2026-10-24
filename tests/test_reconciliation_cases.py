import pytest

from swarm_lab.reconciliation_cases import (
    AS_OF,
    END,
    START,
    ReconciliationWorkspace,
    generate,
    python_total,
)


def test_oracle_selects_revisions_before_filters_and_honors_time_boundaries():
    orders = [(1, "north"), (2, "north")]
    statuses = [(1, 1, START, "active"), (2, 1, START, "active"),
                (2, 2, AS_OF, "cancelled")]
    rows = [
        (1, 1, 1, START, START, "shipment", 100, "posted"),
        (1, 1, 2, AS_OF, END, "shipment", 100, "posted"),  # moves out of period
        (2, 1, 1, START, START, "shipment", 10, "posted"),
        (2, 1, 2, "2026-10-04T00:00:00Z", END, "shipment", 999, "void"),  # future
        (3, 1, 1, START, START, "return", 3, "posted"),
        (4, 2, 1, START, START, "shipment", 999, "posted"),  # cancelled order
    ]
    assert python_total(orders, statuses, rows) == 7


@pytest.mark.parametrize("revision", [1, 2])
def test_truth_changes_data_without_changing_report(revision):
    good, bad = generate(711, True, revision), generate(711, False, revision)
    assert good[3] == bad[3]
    assert good[4] == good[3]["net_shipped_units"]
    assert bad[4] != bad[3]["net_shipped_units"]


@pytest.mark.parametrize("revision", [1, 2])
def test_independent_sql_and_python_oracles_agree_on_generated_databases(revision):
    for seed in range(10):
        for truth in (False, True):
            workspace = ReconciliationWorkspace(seed, truth, revision=revision)
            try:
                assert workspace.expected == workspace.sql_expected
                assert (workspace.expected == workspace.report["net_shipped_units"]) == truth
                assert set(workspace.hashes()) == {
                    "README.md", "records.sqlite", "schema.sql", "report.json",
                    "tests/test_smoke.py"}
            finally:
                workspace.close()


def test_out_of_order_arrival_and_missing_status_have_known_answer():
    orders = [(1, "north"), (2, "north")]
    statuses = [(1, 1, AS_OF, "cancelled"), (1, 2, START, "active")]
    rows = [
        (1, 1, 1, AS_OF, START, "shipment", 100, "posted"),
        (1, 1, 2, START, START, "return", 7, "posted"),
        (2, 2, 1, START, START, "shipment", 999, "posted"),
    ]
    assert python_total(orders, statuses, rows) == -7
