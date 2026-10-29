from datetime import date

import pytest

from ledger import Entry, Ledger


def _ledger() -> Ledger:
    led = Ledger()
    led.post(Entry(date(2024, 1, 10), "cash", 10_000, "opening"))
    led.post(Entry(date(2024, 1, 15), "cash", -2_500, "rent"))
    led.post(Entry(date(2024, 1, 15), "cash", 400, "refund"))
    led.post(Entry(date(2024, 1, 20), "cash", -1_200, "groceries"))
    led.post(Entry(date(2024, 1, 12), "savings", 5_000, "transfer in"))
    return led


def test_balance_all_time():
    assert _ledger().balance("cash") == 6_700


def test_balance_unknown_account_is_zero():
    assert _ledger().balance("nope") == 0


def test_balance_as_of_includes_entries_on_that_day():
    # 10_000 - 2_500 + 400: both Jan 15 entries must be included
    assert _ledger().balance("cash", as_of=date(2024, 1, 15)) == 7_900


def test_statement_filters_by_account_and_sorts():
    rows = _ledger().statement("cash", date(2024, 1, 1), date(2024, 2, 1))
    assert [r.memo for r in rows] == ["opening", "rent", "refund", "groceries"]


def test_post_rejects_non_int_amount():
    with pytest.raises(TypeError):
        Ledger().post(Entry(date(2024, 1, 1), "cash", 1.5))  # type: ignore[arg-type]


def test_accounts_sorted_unique():
    assert _ledger().accounts() == ["cash", "savings"]
