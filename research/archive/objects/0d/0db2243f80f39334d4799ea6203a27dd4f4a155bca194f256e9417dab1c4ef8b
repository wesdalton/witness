"""Held-out inventory reconciliation: generated data with two independent oracles.

This is an authored task family, not an upstream historical software regression.
No model call is made here. It is not yet part of a paid experiment.
"""

from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import tempfile
from pathlib import Path

from swarm_lab.agent_workspace import Workspace
from swarm_lab.portfolio_cases import IMAGE

START = "2026-09-01T00:00:00Z"
END = "2026-10-01T00:00:00Z"
AS_OF = "2026-10-03T00:00:00Z"
SCHEMA = """
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY, warehouse TEXT NOT NULL
);
CREATE TABLE order_status (
    order_id INTEGER NOT NULL, revision INTEGER NOT NULL,
    recorded_at TEXT NOT NULL, state TEXT NOT NULL,
    PRIMARY KEY(order_id, revision)
);
CREATE TABLE movements (
    movement_id INTEGER NOT NULL, order_id INTEGER NOT NULL,
    revision INTEGER NOT NULL, recorded_at TEXT NOT NULL,
    effective_at TEXT NOT NULL, kind TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0), state TEXT NOT NULL,
    PRIMARY KEY(movement_id, revision)
);
"""
CONTRACT = f"""Inventory reconciliation contract

Assess the reported net shipped units for warehouse north for effective times
{START} inclusive through {END} exclusive, using information recorded on or before
{AS_OF} inclusive. All timestamps are UTC ISO strings in one comparable format.

First exclude revisions recorded after the as-of cutoff. For each movement_id,
retain the highest remaining revision number. For each order_id, independently
retain the highest remaining order-status revision number. The selection of latest
revisions happens before filtering movement effective time, movement state, or
order state. A later recorded revision can change the effective time or void a
movement. Revisions recorded after the cutoff must not influence this report.

Include only latest movements whose state is posted, whose effective_at falls in
the stated half-open interval, whose order belongs to warehouse north, and whose
latest known order status is active. Exclude orders without a known status.
Shipments contribute +quantity; returns contribute -quantity. A movement is counted
once, irrespective of how many historical or future revisions are present.

The read-only records.sqlite database is the source of truth. report.json contains
the publisher's disputed total. schema.sql describes the tables. Python and its
sqlite3 standard library are available. You may write and execute your own query.
"""

# Independent implementation of the contract in relational form.
ORACLE_SQL = """
WITH latest_movements AS (
 SELECT *, ROW_NUMBER() OVER (
   PARTITION BY movement_id ORDER BY revision DESC
 ) AS rank FROM movements WHERE recorded_at <= :as_of
), latest_status AS (
 SELECT *, ROW_NUMBER() OVER (
   PARTITION BY order_id ORDER BY revision DESC
 ) AS rank FROM order_status WHERE recorded_at <= :as_of
)
SELECT COALESCE(SUM(CASE WHEN m.kind = 'shipment' THEN m.quantity ELSE -m.quantity END),0)
FROM latest_movements m
JOIN orders o ON o.order_id = m.order_id
JOIN latest_status s ON s.order_id = o.order_id AND s.rank = 1
WHERE m.rank = 1 AND m.state = 'posted' AND s.state = 'active'
AND o.warehouse = 'north' AND m.effective_at >= :start AND m.effective_at < :end
"""


def python_total(orders, statuses, movements):
    warehouses = dict(orders)
    latest_status, latest_movement = {}, {}
    for row in statuses:
        oid, revision, recorded, _ = row
        if recorded <= AS_OF and (oid not in latest_status
                                  or latest_status[oid][1] < revision):
            latest_status[oid] = row
    for row in movements:
        mid, _, revision, recorded, *_ = row
        if recorded <= AS_OF and (mid not in latest_movement
                                  or latest_movement[mid][2] < revision):
            latest_movement[mid] = row
    total = 0
    for _, oid, _, _, effective, kind, quantity, state in latest_movement.values():
        if (warehouses[oid] == "north" and oid in latest_status
                and latest_status[oid][3] == "active" and state == "posted"
                and START <= effective < END):
            total += quantity if kind == "shipment" else -quantity
    return total


def generate(seed, truth, revision=1):
    if type(truth) is not bool:
        raise ValueError("Truth must be boolean")
    if revision not in (1, 2):
        raise ValueError("Unknown generator revision")
    rng = random.Random(f"witness-inventory-v{revision}:{seed}")
    orders, statuses, movements = [], [], []
    dates = ["2026-08-31T23:59:59Z", START, "2026-09-15T12:00:00Z",
             "2026-09-30T23:59:59Z", END, "2026-10-02T12:00:00Z"]
    for oid in range(1, 161):
        orders.append((oid, rng.choice(["north", "north", "south"])))
        statuses.append((oid, 1, "2026-08-01T00:00:00Z", "active"))
        if rng.random() < 0.35:
            statuses.append((oid, 2, "2026-09-25T00:00:00Z", "cancelled"))
        if rng.random() < 0.25:
            statuses.append((oid, 3, "2026-10-04T00:00:00Z", "active"))
        for offset in range(4):
            mid = oid*4 + offset
            kind = rng.choice(["shipment", "shipment", "return"])
            movements.append((mid, oid, 1, "2026-09-10T00:00:00Z",
                              rng.choice(dates), kind, rng.randint(1, 200), "posted"))
            if rng.random() < 0.55:
                movements.append((mid, oid, 2, "2026-10-02T00:00:00Z",
                                  rng.choice(dates), kind, rng.randint(1, 200),
                                  rng.choice(["posted", "posted", "void"])))
            if rng.random() < 0.35:
                movements.append((mid, oid, 3, "2026-10-04T00:00:00Z",
                                  rng.choice(dates), kind, rng.randint(1, 200), "void"))
    # A guaranteed included movement makes the truth-changing perturbation provable.
    anchor_order = 161
    anchor_id = anchor_order*4
    quantity = rng.randint(20, 200)
    orders.append((anchor_order, "north"))
    statuses.append((anchor_order, 1, "2026-08-01T00:00:00Z", "active"))
    anchor = (anchor_id, anchor_order, 1, AS_OF, START, "shipment", quantity, "posted")
    movements.append(anchor)
    movements.append((anchor_id, anchor_order, 2, "2026-10-04T00:00:00Z",
                      END, "shipment", quantity, "void"))
    if revision == 2:
        # Version numbers, not arrival timestamps, determine the winning revision.
        # Also exercise an order without known status and a change in movement kind.
        for extra_oid in (162, 163, 164):
            orders.append((extra_oid, "north"))
        statuses.extend([
            (162, 1, "2026-09-20T00:00:00Z", "cancelled"),
            (162, 2, "2026-09-01T00:00:00Z", "active"),
            (164, 1, "2026-08-01T00:00:00Z", "active"),
        ])
        a, b, c = (rng.randint(20, 200) for _ in range(3))
        movements.extend([
            (648, 162, 1, "2026-09-20T00:00:00Z", START, "shipment", a, "posted"),
            (648, 162, 2, "2026-09-01T00:00:00Z", START, "return", b, "posted"),
            (652, 163, 1, "2026-09-10T00:00:00Z", START, "shipment", c, "posted"),
            (656, 164, 1, "2026-09-20T00:00:00Z", START, "shipment", a, "posted"),
            (656, 164, 2, "2026-09-01T00:00:00Z", START, "return", b, "posted"),
        ])
    reported = python_total(orders, statuses, movements)
    delta = rng.choice([-1, 1]) * rng.randint(1, min(19, quantity-1))
    if not truth:
        index = movements.index(anchor)
        movements[index] = (*anchor[:6], quantity+delta, anchor[7])
    rng.shuffle(orders)
    rng.shuffle(statuses)
    rng.shuffle(movements)
    actual = python_total(orders, statuses, movements)
    assert actual == reported + (0 if truth else delta)
    report = {"warehouse": "north", "effective_start_inclusive": START,
              "effective_end_exclusive": END, "recorded_as_of_inclusive": AS_OF,
              "net_shipped_units": reported}
    return orders, statuses, movements, report, actual


class ReconciliationWorkspace(Workspace):
    def __init__(self, seed, truth, image=IMAGE, revision=1):
        self.tmp = tempfile.TemporaryDirectory(prefix="witness-case-")
        self.path = Path(self.tmp.name)
        self.path.chmod(0o755)
        self.image = image
        orders, statuses, movements, self.report, self.expected = generate(seed, truth, revision)
        (self.path / "README.md").write_text(CONTRACT)
        (self.path / "schema.sql").write_text(SCHEMA)
        (self.path / "report.json").write_text(json.dumps(self.report, indent=2) + "\n")
        (self.path / "tests").mkdir()
        (self.path / "tests/test_smoke.py").write_text(
            "import sqlite3\n\ndef test_database_integrity():\n"
            "    with sqlite3.connect('file:records.sqlite?mode=ro', uri=True) as db:\n"
            "        assert db.execute('PRAGMA quick_check').fetchone() == ('ok',)\n")
        with sqlite3.connect(self.path / "records.sqlite") as db:
            db.executescript(SCHEMA)
            db.executemany("INSERT INTO orders VALUES (?,?)", orders)
            db.executemany("INSERT INTO order_status VALUES (?,?,?,?)", statuses)
            db.executemany("INSERT INTO movements VALUES (?,?,?,?,?,?,?,?)", movements)
            self.sql_expected = db.execute(
                ORACLE_SQL, {"as_of": AS_OF, "start": START, "end": END}).fetchone()[0]
        if self.sql_expected != self.expected:
            self.close()
            raise ValueError("Independent reconciliation oracles disagree")

    def hashes(self):
        return {str(p.relative_to(self.path)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(self.path.rglob("*")) if p.is_file()}


def verify_generated(seeds, revision=1):
    results = []
    for seed in seeds:
        reports = []
        for truth in (True, False):
            workspace = ReconciliationWorkspace(seed, truth, revision=revision)
            try:
                reports.append(workspace.report)
                assert (workspace.sql_expected == workspace.report["net_shipped_units"]) == truth
                results.append({"seed": seed, "truth": truth, "generator_revision": revision,
                                "python_total": workspace.expected,
                                "sql_total": workspace.sql_expected,
                                "reported_total": workspace.report["net_shipped_units"],
                                "source_sha256": workspace.hashes()})
            finally:
                workspace.close()
        if reports[0] != reports[1]:
            raise ValueError("Truth leaked through the initial report")
    return results
