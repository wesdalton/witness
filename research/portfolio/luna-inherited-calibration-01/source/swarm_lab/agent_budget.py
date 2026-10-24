"""Persistent, conservative reservation accounting for the $25 research phase."""

from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from swarm_lab.pilot import BudgetError, money

PHASE_LIMIT = Decimal("25")
HEADER = {
    "type": "authorization",
    "schema": "witness.agent-budget.v1",
    "phase": "live-verification-20261024",
    "limit_usd": "25",
    "source": "User authorized $25 for the pilot and follow-up replications, 2026-10-24",
}


class PhaseBudget:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        with os.fdopen(fd, "r+", encoding="utf-8") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                raw = stream.read()
                if raw and not raw.endswith("\n"):
                    raise BudgetError("Incomplete phase ledger; reconcile before spending")
                try:
                    rows = [json.loads(line) for line in raw.splitlines()]
                except json.JSONDecodeError as exc:
                    raise BudgetError("Invalid phase ledger") from exc
                if rows and rows[0] != HEADER:
                    raise BudgetError("Unknown phase authorization")

                def append(row):
                    row = {**row, "at": datetime.now(UTC).isoformat()}
                    stream.seek(0, os.SEEK_END)
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                    rows.append(row)

                if not rows:
                    # Header has no variable timestamp so that identity is exact.
                    stream.write(json.dumps(HEADER) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                    rows.append(HEADER)
                yield rows, append
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def reserve(self, request: str, batch: str, amount: Decimal, batch_limit: Decimal):
        amount, batch_limit = money(amount), money(batch_limit)
        if not 0 < amount <= batch_limit <= PHASE_LIMIT:
            raise BudgetError("Invalid reservation or batch ceiling")
        with self.transaction() as (rows, append):
            reserves = [r for r in rows if r["type"] == "reserve"]
            if any(r["request"] == request for r in reserves):
                raise BudgetError("Request already reserved; no retries")
            total = sum((money(r["usd"]) for r in reserves), Decimal(0))
            batch_total = sum(
                (money(r["usd"]) for r in reserves if r["batch"] == batch), Decimal(0)
            )
            completed = {r["request"]: r for r in rows if r["type"] == "complete"}
            if any(
                r["request"] not in completed
                or completed[r["request"]]["status"] != "ok"
                for r in reserves
            ):
                raise BudgetError("Unreconciled or failed request; review before more spending")
            if total + amount > PHASE_LIMIT or batch_total + amount > batch_limit:
                raise BudgetError("Phase or batch reservation ceiling reached")
            append({"type": "reserve", "request": request, "batch": batch, "usd": str(amount)})

    def complete(self, request: str, status: str, cost=None, usage=None, response_id=None):
        with self.transaction() as (rows, append):
            reservation = next(
                (r for r in rows if r["type"] == "reserve" and r["request"] == request), None
            )
            if reservation is None or any(
                r["type"] == "complete" and r["request"] == request for r in rows
            ):
                raise BudgetError("Unknown or already completed request")
            if cost is not None and money(cost) > money(reservation["usd"]):
                status = "billing_overrun"
            append({
                "type": "complete", "request": request, "status": status,
                "reported_cost_usd": str(money(cost)) if cost is not None else None,
                "usage": usage, "response_id": response_id, "reservation_retained": True,
            })
            if status != "ok":
                raise BudgetError(f"Request requires review: {status}")

    def summary(self):
        with self.transaction() as (rows, _):
            return {
                "phase_limit_usd": str(PHASE_LIMIT),
                "requests": sum(r["type"] == "reserve" for r in rows),
                "reserved_usd": str(sum(
                    (money(r["usd"]) for r in rows if r["type"] == "reserve"), Decimal(0)
                )),
                "reported_cost_usd": str(sum(
                    (money(r["reported_cost_usd"]) for r in rows
                     if r["type"] == "complete" and r["reported_cost_usd"] is not None),
                    Decimal(0),
                )),
            }
