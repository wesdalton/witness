"""A minimal double-entry-free ledger: append-only entries, per-account balances.

See TASK.md for the behavioural spec.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Entry:
    posted_on: date
    account: str
    amount_cents: int
    memo: str = ""


class Ledger:
    def __init__(self) -> None:
        self._entries: list[Entry] = []

    def post(self, entry: Entry) -> None:
        if not entry.account:
            raise ValueError("account is required")
        if not isinstance(entry.amount_cents, int) or isinstance(entry.amount_cents, bool):
            raise TypeError("amount_cents must be an int")
        self._entries.append(entry)

    def accounts(self) -> list[str]:
        return sorted({e.account for e in self._entries})

    def balance(self, account: str, as_of: date | None = None) -> int:
        """Sum of amount_cents for `account` dated on or before `as_of` (all dates if None)."""
        return sum(
            e.amount_cents
            for e in self._entries
            if e.account == account and _within(e, date.min, as_of)
        )

    def statement(self, account: str, start: date, end: date) -> list[Entry]:
        """Entries for `account` dated within [start, end], sorted by date (stable)."""
        rows = [e for e in self._entries if e.account == account and _within(e, start, end)]
        return sorted(rows, key=lambda e: e.posted_on)


def _within(entry: Entry, start: date, end: date | None) -> bool:
    if entry.posted_on < start:
        return False
    if end is None:
        return True
    return entry.posted_on < end
