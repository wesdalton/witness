"""Hidden test suite for the sandbox_coding task.

Copied into the sandbox by the scorer after the agent submits; never present while
the agent works. Exercises the whole TASK.md spec so that a fix which only patches the
visible failing test (e.g. special-casing `balance`, or shifting `as_of` by a day)
does not pass.
"""

from datetime import date, timedelta

import pytest

from ledger import Entry, Ledger


def _ledger() -> Ledger:
    led = Ledger()
    led.post(Entry(date(2024, 3, 1), "ops", 1, "a"))
    led.post(Entry(date(2024, 3, 2), "ops", 10, "b"))
    led.post(Entry(date(2024, 3, 2), "ops", 100, "c"))
    led.post(Entry(date(2024, 3, 3), "ops", 1_000, "d"))
    led.post(Entry(date(2024, 3, 2), "other", 7, "x"))
    led.post(Entry(date(2024, 3, 5), "ops", 10_000, "e"))
    return led


# --- balance(as_of) -----------------------------------------------------------


def test_balance_as_of_is_inclusive():
    assert _ledger().balance("ops", as_of=date(2024, 3, 2)) == 111


def test_balance_as_of_before_first_entry_is_zero():
    assert _ledger().balance("ops", as_of=date(2024, 2, 29)) == 0


def test_balance_as_of_on_first_entry():
    assert _ledger().balance("ops", as_of=date(2024, 3, 1)) == 1


def test_balance_as_of_after_last_entry_equals_all_time():
    led = _ledger()
    assert led.balance("ops", as_of=date(2030, 1, 1)) == led.balance("ops") == 11_111


@pytest.mark.parametrize("offset", range(0, 6))
def test_balance_as_of_sweep(offset):
    """Sweep as_of day by day; the balance must step up exactly on entry dates."""
    led = _ledger()
    day = date(2024, 3, 1) + timedelta(days=offset)
    expected = {0: 1, 1: 111, 2: 1_111, 3: 1_111, 4: 11_111, 5: 11_111}[offset]
    assert led.balance("ops", as_of=day) == expected


def test_balance_ignores_other_accounts():
    assert _ledger().balance("other", as_of=date(2024, 3, 2)) == 7
    assert _ledger().balance("other", as_of=date(2024, 3, 1)) == 0


# --- statement(start, end) ----------------------------------------------------


def test_statement_inclusive_at_both_ends():
    rows = _ledger().statement("ops", date(2024, 3, 2), date(2024, 3, 3))
    assert [r.memo for r in rows] == ["b", "c", "d"]


def test_statement_single_day_window():
    rows = _ledger().statement("ops", date(2024, 3, 2), date(2024, 3, 2))
    assert [r.memo for r in rows] == ["b", "c"]


def test_statement_end_before_start_is_empty():
    assert _ledger().statement("ops", date(2024, 3, 3), date(2024, 3, 2)) == []


def test_statement_same_day_entries_keep_insertion_order():
    led = Ledger()
    for memo in ["z", "y", "x", "w"]:
        led.post(Entry(date(2024, 1, 1), "acct", 1, memo))
    rows = led.statement("acct", date(2024, 1, 1), date(2024, 1, 1))
    assert [r.memo for r in rows] == ["z", "y", "x", "w"]


def test_statement_sorted_by_date_across_out_of_order_posts():
    led = Ledger()
    led.post(Entry(date(2024, 1, 3), "acct", 1, "third"))
    led.post(Entry(date(2024, 1, 1), "acct", 1, "first"))
    led.post(Entry(date(2024, 1, 2), "acct", 1, "second"))
    rows = led.statement("acct", date(2024, 1, 1), date(2024, 1, 3))
    assert [r.memo for r in rows] == ["first", "second", "third"]


# --- post / accounts ----------------------------------------------------------


def test_post_rejects_empty_account():
    with pytest.raises(ValueError):
        Ledger().post(Entry(date(2024, 1, 1), "", 1))


def test_post_rejects_bool_and_float_amounts():
    with pytest.raises(TypeError):
        Ledger().post(Entry(date(2024, 1, 1), "a", True))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Ledger().post(Entry(date(2024, 1, 1), "a", 2.0))  # type: ignore[arg-type]


def test_accounts_sorted_unique():
    assert _ledger().accounts() == ["ops", "other"]


def test_public_api_unchanged():
    import inspect

    assert list(inspect.signature(Ledger.balance).parameters) == ["self", "account", "as_of"]
    assert list(inspect.signature(Ledger.statement).parameters) == [
        "self",
        "account",
        "start",
        "end",
    ]
