"""Bounded sequentially consistent schedules, with independent exact references."""

from __future__ import annotations

import hashlib
import itertools
import json
import random
import sqlite3
import tempfile
from functools import lru_cache
from pathlib import Path

from swarm_lab.legacy.agent_workspace import Workspace
from swarm_lab.legacy.portfolio_cases import IMAGE
from swarm_lab.legacy.reconciliation_query import execute_query, scalar_result

LIVE_HOLD_REASON = "Schedule capability pilot completed at ceiling; no further paid batch selected"
SCHEMA = """
CREATE TABLE workers(worker INTEGER PRIMARY KEY, delta INTEGER NOT NULL);
CREATE TABLE operations(op INTEGER PRIMARY KEY, worker INTEGER NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('read','write')), UNIQUE(worker,kind));
CREATE TABLE ordering(before_op INTEGER NOT NULL, after_op INTEGER NOT NULL,
 PRIMARY KEY(before_op,after_op));
"""
CONTRACT = """Concurrent shared-balance outcome audit

The database is the complete source of truth. There are one to four workers,
with distinct worker IDs in 0..3. Each has exactly one read and one write operation.
Operation IDs are distinct integers in 0..15 and do not imply execution order.
Each worker has an integer delta in -9..9, including zero. The shared balance starts
at :initial_balance, an integer in -100..100. Each worker has its own private register.

A legal schedule executes every operation exactly once in a total order respecting
every edge in ordering. The ordering graph is acyclic and explicitly includes
each worker's read-before-write edge. Other edges may constrain different workers.
Each operation is atomic; a worker's read/write pair is NOT atomic. A read copies
the CURRENT shared balance into that worker's private register. A write REPLACES
the shared balance with that worker's previously read register plus its delta.
Other workers' intervening writes do not change a saved private register.
This is sequential consistency; there are no weak-memory effects or other actions.

Compute the minimum final shared balance over ALL legal complete schedules.
At least one legal complete schedule exists. The publisher reports that this
minimum equals its minimum_final_balance. Its execution receipt records one
actual legal schedule and its result; it is not an exhaustive exploration.
Assess the finite claim and construct your own verification program. No solver
implementation is supplied. Return the exact integer minimum, not a count,
the sum of deltas, a partial-schedule value, or the outcome of only one schedule.
"""
ORACLE_SQL = """
WITH RECURSIVE
requirements AS (
 SELECT o.op, o.worker, o.kind, w.delta,
        COALESCE((SELECT SUM(1 << d.before_op) FROM ordering d
                  WHERE d.after_op=o.op),0) AS needed
 FROM operations o JOIN workers w ON w.worker=o.worker
),
states(done,balance,r0,r1,r2,r3) AS (
 SELECT 0, :initial_balance, 0, 0, 0, 0
 UNION
 SELECT s.done | (1 << o.op),
        CASE WHEN o.kind='write' THEN
          CASE o.worker WHEN 0 THEN s.r0 WHEN 1 THEN s.r1
                        WHEN 2 THEN s.r2 ELSE s.r3 END + o.delta
          ELSE s.balance END,
        CASE WHEN o.kind='read' AND o.worker=0 THEN s.balance ELSE s.r0 END,
        CASE WHEN o.kind='read' AND o.worker=1 THEN s.balance ELSE s.r1 END,
        CASE WHEN o.kind='read' AND o.worker=2 THEN s.balance ELSE s.r2 END,
        CASE WHEN o.kind='read' AND o.worker=3 THEN s.balance ELSE s.r3 END
 FROM states s JOIN requirements o
 ON (s.done & (1 << o.op))=0 AND (s.done & o.needed)=o.needed
)
SELECT MIN(balance) FROM states
WHERE done=(SELECT SUM(1 << op) FROM operations)
"""
RECEIPT_DRIVER = """
import json
import sqlite3

spec = json.load(open("publisher_schedule.json"))
with sqlite3.connect("file:records.sqlite?mode=ro", uri=True) as db:
    workers = dict(db.execute("SELECT worker,delta FROM workers"))
    operations = {op: (worker, kind) for op, worker, kind in
                  db.execute("SELECT op,worker,kind FROM operations")}
    ordering = list(db.execute("SELECT before_op,after_op FROM ordering"))
schedule = spec["schedule"]
assert len(schedule) == len(operations) and set(schedule) == set(operations)
positions = {op: i for i, op in enumerate(schedule)}
assert all(positions[a] < positions[b] for a, b in ordering)
shared, registers, trace = spec["initial_balance"], {}, []
for op in schedule:
    worker, kind = operations[op]
    if kind == "read":
        registers[worker] = shared
    else:
        shared = registers[worker] + workers[worker]
    trace.append({"op": op, "worker": worker, "kind": kind, "balance_after": shared})
print(json.dumps({"schedule": schedule, "steps": trace, "final_balance": shared}))
"""


def validate_instance(workers, operations, ordering, initial):
    worker_ids = [w for w, _ in workers]
    op_ids = [o for o, _, _ in operations]
    if (not 1 <= len(workers) <= 4 or len(set(worker_ids)) != len(workers)
            or any(type(w) is not int or not 0 <= w <= 3
                   or type(d) is not int or not -9 <= d <= 9 for w, d in workers)
            or type(initial) is not int or not -100 <= initial <= 100):
        raise ValueError("Invalid worker/numeric domain")
    if (len(operations) != 2*len(workers) or len(set(op_ids)) != len(op_ids)
            or any(type(o) is not int or not 0 <= o <= 15 or type(w) is not int
                   or w not in worker_ids or kind not in ("read", "write")
                   for o, w, kind in operations)):
        raise ValueError("Invalid operation domain")
    for w in worker_ids:
        ops = [(o, kind) for o, worker, kind in operations if worker == w]
        if sorted(kind for _, kind in ops) != ["read", "write"]:
            raise ValueError("Each worker needs one read and write")
        ids = {kind: op for op, kind in ops}
        if (ids["read"], ids["write"]) not in ordering:
            raise ValueError("Missing read-before-write edge")
    if (len(set(ordering)) != len(ordering) or any(
            type(a) is not int or type(b) is not int or a not in op_ids or b not in op_ids
            for a, b in ordering)):
        raise ValueError("Invalid ordering edge")
    pending, done = set(op_ids), set()
    while pending:
        ready = {o for o in pending if all(a in done for a, b in ordering if b == o)}
        if not ready:
            raise ValueError("Ordering graph must be acyclic")
        pending -= ready
        done |= ready


def explore_outcomes(workers, operations, ordering, initial):
    """Memoized transition exploration using Python sets and private-register tuples."""
    deltas = dict(workers)
    predecessors = {o: frozenset(a for a, b in ordering if b == o)
                    for o, _, _ in operations}
    op_map = {o: (w, kind) for o, w, kind in operations}
    all_ops = frozenset(op_map)

    @lru_cache(None)
    def visit(done, balance, registers):
        if done == all_ops:
            return frozenset((balance,))
        outcomes = set()
        for op in all_ops - done:
            if not predecessors[op] <= done:
                continue
            w, kind = op_map[op]
            updated = list(registers)
            next_balance = balance
            if kind == "read":
                updated[w] = balance
            else:
                if registers[w] is None:
                    raise ValueError("Write before read")
                next_balance = registers[w] + deltas[w]
            outcomes.update(visit(done | {op}, next_balance, tuple(updated)))
        return frozenset(outcomes)

    values = visit(frozenset(), initial, (None,)*4)
    if not values:
        raise ValueError("No complete schedule")
    return values


def execute_schedule(workers, operations, ordering, initial, schedule):
    """Independent straight-line interpreter for a supplied complete schedule."""
    if len(schedule) != len(operations) or set(schedule) != {o for o, _, _ in operations}:
        raise ValueError("Schedule does not execute every operation once")
    positions = {o: i for i, o in enumerate(schedule)}
    if any(positions[a] >= positions[b] for a, b in ordering):
        raise ValueError("Schedule violates ordering")
    registers, shared, trace = {}, initial, []
    for op in schedule:
        _, worker, kind = next(row for row in operations if row[0] == op)
        delta = next(d for w, d in workers if w == worker)
        if kind == "read":
            registers[worker] = shared
        else:
            shared = registers[worker] + delta
        trace.append({"op": op, "worker": worker, "kind": kind, "balance_after": shared})
    return {"schedule": list(schedule), "steps": trace, "final_balance": shared}


def permutation_outcomes(workers, operations, ordering, initial):
    """Brute-force total-order enumeration, independent of recursive state merging."""
    outcomes = set()
    for schedule in itertools.permutations(o for o, _, _ in operations):
        positions = {op: i for i, op in enumerate(schedule)}
        if any(positions[a] >= positions[b] for a, b in ordering):
            continue
        outcomes.add(execute_schedule(workers, operations, ordering, initial, schedule)[
            "final_balance"])
    return outcomes


def make_database(path, workers, operations, ordering):
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO workers VALUES (?,?)", workers)
        db.executemany("INSERT INTO operations VALUES (?,?,?)", operations)
        db.executemany("INSERT INTO ordering VALUES (?,?)", ordering)


def generated_instance(seed, truth):
    rng = random.Random(f"witness-schedules-v1:{seed}")
    workers = [(w, rng.choice([d for d in range(-5, 8) if d])) for w in range(4)]
    ids = rng.sample(range(16), 8)
    operations = [(ids[2*w+i], w, kind) for w in range(4)
                  for i, kind in enumerate(("read", "write"))]
    canonical = [op for op, _, _ in operations]
    initial = rng.randint(-20, 30)
    published = initial + sum(d for _, d in workers)
    required = {(ids[2*w], ids[2*w+1]) for w in range(4)}
    for candidate in range(2000):
        density = (0.15, 0.35, 0.65)[candidate % 3]
        ordering = sorted(required | {(canonical[i], canonical[j])
                                     for i in range(8) for j in range(i+1, 8)
                                     if rng.random() < density})
        values = explore_outcomes(workers, operations, ordering, initial)
        if (min(values) == published) == truth:
            validate_instance(workers, operations, ordering, initial)
            return {"workers": workers, "operations": operations, "ordering": ordering,
                    "initial": initial, "canonical": canonical, "candidate": candidate,
                    "expected": min(values), "published": published}
    raise ValueError("No reference-qualified finite claim")


class ScheduleDatabase(Workspace):
    contract, schema = CONTRACT, SCHEMA
    claim = ("The publisher's minimum_final_balance is the minimum "
             "over all legal complete schedules.")

    def __init__(self, workers, operations, ordering, initial, image=IMAGE):
        validate_instance(workers, operations, ordering, initial)
        values = explore_outcomes(workers, operations, ordering, initial)
        self.expected = min(values)
        self.parameters = {"initial_balance": initial}
        self.tmp = tempfile.TemporaryDirectory(prefix="witness-schedules-")
        self.path = Path(self.tmp.name)
        self.path.chmod(0o755)
        self.image = image
        make_database(self.path / "records.sqlite", workers, operations, ordering)
        with sqlite3.connect(self.path / "records.sqlite") as db:
            actual = db.execute(ORACLE_SQL, self.parameters).fetchone()[0]
        if type(actual) is not int or actual != self.expected:
            self.close()
            raise ValueError("Independent SQL/state references disagree")
        (self.path / "README.md").write_text(CONTRACT)
        (self.path / "schema.sql").write_text(SCHEMA)

    def hashes(self):
        return {str(p.relative_to(self.path)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(self.path.rglob("*")) if p.is_file()}


class ScheduleWorkspace(ScheduleDatabase):
    def __init__(self, seed, truth, image=IMAGE):
        if type(truth) is not bool:
            raise ValueError("Truth must be boolean")
        spec = generated_instance(seed, truth)
        super().__init__(spec["workers"], spec["operations"], spec["ordering"],
                         spec["initial"], image)
        if permutation_outcomes(spec["workers"], spec["operations"], spec["ordering"],
                                spec["initial"]) != explore_outcomes(
                spec["workers"], spec["operations"], spec["ordering"], spec["initial"]):
            self.close()
            raise ValueError("Independent permutation reference disagrees")
        expected_receipt = execute_schedule(
            spec["workers"], spec["operations"], spec["ordering"],
            spec["initial"], spec["canonical"])
        (self.path / "publisher_schedule.json").write_text(json.dumps(
            {"initial_balance": spec["initial"], "schedule": spec["canonical"]}))
        (self.path / "publisher_receipt.py").write_text(RECEIPT_DRIVER)
        run = self.execute(["python", "publisher_receipt.py"])
        if run["exit_code"] or run["timed_out"] or run["output_truncated"]:
            self.close()
            raise ValueError("Live publisher schedule interpreter failed")
        actual_receipt = json.loads(run["stdout"])
        if actual_receipt != expected_receipt:
            self.close()
            raise ValueError("Live receipt disagrees with independent interpreter")
        self.publisher_execution = {
            "scope": "One complete schedule executed by a finite-model interpreter, not OS threads",
            "result": actual_receipt, "exit_code": run["exit_code"]}
        published = actual_receipt["final_balance"]
        if (published == self.expected) != truth:
            self.close()
            raise ValueError("Publisher does not realize planned finite label")
        self.report = {"minimum_final_balance": published}
        (self.path / "report.json").write_text(json.dumps(self.report, indent=2) + "\n")
        (self.path / "tests").mkdir()
        (self.path / "tests/test_smoke.py").write_text(
            "import sqlite3\n\ndef test_database_integrity():\n"
            "    with sqlite3.connect('file:records.sqlite?mode=ro', uri=True) as db:\n"
            "        assert db.execute('PRAGMA quick_check').fetchone() == ('ok',)\n")


def verify_generated(seeds, image=IMAGE):
    rows = []
    for seed in seeds:
        views = []
        for truth in (False, True):
            workspace = ScheduleWorkspace(seed, truth, image)
            try:
                result = execute_query(workspace, ORACLE_SQL)
                if scalar_result(result) != workspace.expected:
                    raise ValueError("Live schedule reference failed")
                views.append((workspace.report, workspace.publisher_execution,
                              workspace.parameters))
                rows.append({"seed": seed, "truth": truth, "expected": workspace.expected,
                             "report": workspace.report, "reference_execution": result,
                             "workspace_sha256": workspace.hashes()})
            finally:
                workspace.close()
        if views[0] != views[1]:
            raise ValueError("Initial execution evidence reveals finite truth")
    return rows


def replay_worlds(seeds):
    worlds = []
    for seed in seeds:
        for truth in (False, True):
            worlds.append({"name": f"generated-{seed}-{truth}", **generated_instance(seed, truth)})
    for deltas, initial in [((3,), 100), ((0,), -100), ((3, 5), 0),
                            ((-3, -5), 0), ((-3, 5), 17), ((0, 0, 0, 0), -17),
                            ((9, 9, 9, 9), 100), ((-9, -9, -9, -9), -100)]:
        workers = [(3-w, d) for w, d in enumerate(deltas)]
        operations = [(15-2*i-j, w, kind) for i, (w, _) in enumerate(workers)
                      for j, kind in enumerate(("read", "write"))]
        ordering = [(operations[2*i][0], operations[2*i+1][0]) for i in range(len(workers))]
        worlds.append({"name": f"boundary-{deltas}-{initial}", "workers": workers,
                       "operations": operations, "ordering": ordering, "initial": initial})
    return worlds
