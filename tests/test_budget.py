"""Phase budget settlement, ceilings and fail-closed ledger handling."""

import json
from decimal import Decimal

import pytest

from swarm_lab.core.budget import BudgetError, PhaseBudget


def test_phase_budget_settles_successful_requests_to_reported_cost(tmp_path):
    budget = PhaseBudget(tmp_path / "budget.jsonl")
    budget.reserve("one", "batch", Decimal("20"), Decimal("25"))
    budget.complete("one", "ok", cost="0.01", usage={})
    budget.reserve("two", "different-batch", Decimal("6"), Decimal("25"))
    summary = budget.summary()
    assert summary["reserved_usd"] == "26"
    assert summary["reported_cost_usd"] == "0.01"
    # "two" is outstanding, so it still counts at its full reservation.
    assert Decimal(summary["exposure_usd"]) == Decimal("6.01")
    budget.complete("two", "ok", cost="0.02", usage={})
    with pytest.raises(BudgetError, match="ceiling"):
        budget.reserve("three", "batch", Decimal("24.98"), Decimal("25"))
    budget.reserve("four", "batch", Decimal("24.97"), Decimal("25"))


def test_batch_ceiling_uses_settled_batch_exposure(tmp_path):
    budget = PhaseBudget(tmp_path / "budget.jsonl")
    budget.reserve("one", "batch", Decimal("0.5"), Decimal("1"))
    budget.complete("one", "ok", cost="0.1", usage={})
    budget.reserve("two", "batch", Decimal("0.9"), Decimal("1"))
    budget.complete("two", "ok", cost="0.1", usage={})
    with pytest.raises(BudgetError, match="ceiling"):
        budget.reserve("three", "batch", Decimal("0.81"), Decimal("1"))


def test_failed_request_keeps_full_reservation(tmp_path):
    budget = PhaseBudget(tmp_path / "budget.jsonl")
    budget.reserve("one", "batch", Decimal("0.4"), Decimal("1"))
    with pytest.raises(BudgetError, match="review"):
        budget.complete("one", "provider_error:http_500")
    rows = [json.loads(line) for line in (tmp_path / "budget.jsonl").read_text().splitlines()]
    assert rows[-1]["reservation_retained"] is True
    assert budget.summary()["exposure_usd"] == "0.4"

def test_phase_budget_retains_uncertain_dispatch_and_blocks_retries(tmp_path):
    budget = PhaseBudget(tmp_path / "budget.jsonl")
    budget.reserve("one", "batch", Decimal("0.1"), Decimal("1"))
    with pytest.raises(BudgetError, match="already reserved"):
        budget.reserve("one", "batch", Decimal("0.1"), Decimal("1"))
    with pytest.raises(BudgetError, match="Unreconciled"):
        budget.reserve("two", "batch", Decimal("0.1"), Decimal("1"))
    assert budget.summary()["requests"] == 1


def test_batch_limit_and_billing_overrun_stop_spending(tmp_path):
    budget = PhaseBudget(tmp_path / "budget.jsonl")
    budget.reserve("one", "batch", Decimal("0.1"), Decimal("0.1"))
    with pytest.raises(BudgetError, match="billing_overrun"):
        budget.complete("one", "ok", cost="0.2", usage={})
    with pytest.raises(BudgetError, match="failed request"):
        budget.reserve("two", "another-batch", Decimal("0.1"), Decimal("1"))


def test_partial_ledger_fails_closed(tmp_path):
    path = tmp_path / "budget.jsonl"
    path.write_text('{"type":')
    with pytest.raises(BudgetError, match="Incomplete"):
        PhaseBudget(path).summary()
