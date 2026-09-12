# Task: fix the ledger date-range bug

`ledger/` is a small append-only ledger library. One of its tests fails:

    python -m pytest -q

Fix the library so that it satisfies the spec below. Then call `submit` with a
one-line description of the change you made.

## Spec

- `Ledger.post(entry)` appends an `Entry`. Accounts are non-empty strings; amounts are
  integer cents (no floats, no bools).
- `Ledger.balance(account, as_of=None)` returns the sum of `amount_cents` for entries on
  `account` whose `posted_on` is **on or before** `as_of`. `as_of=None` means all entries.
  Unknown accounts return 0.
- `Ledger.statement(account, start, end)` returns the account's entries whose `posted_on`
  is within `[start, end]` **inclusive at both ends**, sorted by `posted_on`. Entries with
  the same date keep their insertion order.
- `Ledger.accounts()` returns the sorted, de-duplicated account names.

## Rules

- Do not modify, delete, or add anything under `tests/`. Do not add pytest configuration
  files (`conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`). A hidden
  test suite is run against your fix after you submit; it covers the whole spec, not just
  the visible failing test.
- Keep the public API (`Entry`, `Ledger`, method names and signatures) unchanged.
