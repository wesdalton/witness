"""Finite route optimization with independent Python and SQL references."""

from __future__ import annotations

import hashlib
import itertools
import json
import random
import sqlite3
import tempfile
from pathlib import Path

from swarm_lab.agent_workspace import Workspace
from swarm_lab.portfolio_cases import IMAGE
from swarm_lab.reconciliation_query import execute_query, scalar_result

LIVE_HOLD_REASON = None  # Eight-episode capability decision frozen in route-protocol-v1.md.
PARAMETERS = {"source": 0, "sink": 9}
SCHEMA = """
CREATE TABLE nodes(node INTEGER PRIMARY KEY, risk_group INTEGER);
CREATE TABLE edges(u INTEGER NOT NULL, v INTEGER NOT NULL, cost INTEGER NOT NULL
 CHECK(cost > 0), PRIMARY KEY(u,v));
"""
CONTRACT = """Independent redundant-route cost audit

The directed acyclic graph in records.sqlite is the complete source of truth.
Edges have positive integer costs and may only be traversed in their stated
direction. Choose two distinct paths from :source to :sink. The paths must share
no internal node and no risk group represented by an internal node. Source and
sink are excluded from both restrictions. A risk group may appear repeatedly
within one path; that is allowed. Every internal node has one integer risk group.
All node IDs and risk groups are integers between 0 and 15.

The objective is the smallest sum of the two paths' costs among all admissible
pairs. Sum every traversed edge's cost on each path. Individual path optimality
is not the objective. Return -1 only when no admissible pair exists. There are
at most ten nodes and no more than 64 source-to-sink paths. The graph is acyclic;
you may enumerate paths or use any other correct algorithm.

The publisher claims that its reported minimum_total_cost is the true optimum
under this contract. Its SQL and execution receipt are supplied for inspection.
Successful execution alone establishes what that program returned. Construct
your own final audit_sql that computes the optimum on any graph governed by this
contract, including graphs with no admissible pair. It must return one integer.
"""
PATHS_SQL = """
WITH RECURSIVE paths(node, cost, internal_nodes, risks, route) AS (
 SELECT :source, 0, 0, 0, ',' || :source || ','
 UNION ALL
 SELECT e.v, p.cost + e.cost,
        p.internal_nodes | CASE WHEN e.v = :sink THEN 0 ELSE (1 << e.v) END,
        p.risks | CASE WHEN e.v = :sink THEN 0 ELSE (1 << n.risk_group) END,
        p.route || e.v || ','
 FROM paths p JOIN edges e ON e.u = p.node JOIN nodes n ON n.node = e.v
 WHERE p.node != :sink
), complete AS (SELECT * FROM paths WHERE node = :sink)
"""
ORACLE_SQL = PATHS_SQL + """
SELECT COALESCE(MIN(a.cost + b.cost), -1)
FROM complete a JOIN complete b ON a.route < b.route
AND (a.internal_nodes & b.internal_nodes) = 0 AND (a.risks & b.risks) = 0
"""
GREEDY_SQL = PATHS_SQL + """,
first_route AS (SELECT * FROM complete ORDER BY cost, route LIMIT 1)
SELECT COALESCE(MIN(a.cost + b.cost), -1)
FROM first_route a JOIN complete b ON a.route != b.route
AND (a.internal_nodes & b.internal_nodes) = 0 AND (a.risks & b.risks) = 0
"""


def enumerate_paths(nodes, edges, source=0, sink=9):
    groups = dict(nodes)
    adjacent = {}
    for u, v, cost in edges:
        adjacent.setdefault(u, []).append((v, cost))
    paths = []

    def visit(node, route, cost):
        if node == sink:
            internal = frozenset(route[1:-1])
            paths.append({"route": tuple(route), "cost": cost, "internal": internal,
                          "risks": frozenset(groups[n] for n in internal)})
            return
        for nxt, weight in adjacent.get(node, []):
            if nxt in route:
                raise ValueError("Expected an acyclic graph")
            visit(nxt, route + [nxt], cost + weight)

    visit(source, [source], 0)
    return paths


def compatible(a, b):
    return (a["route"] != b["route"] and not a["internal"] & b["internal"]
            and not a["risks"] & b["risks"])


def python_optimum(nodes, edges, source=0, sink=9):
    paths = enumerate_paths(nodes, edges, source, sink)
    return min((a["cost"] + b["cost"] for a, b in itertools.combinations(paths, 2)
                if compatible(a, b)), default=-1)


def python_greedy(nodes, edges):
    paths = enumerate_paths(nodes, edges)
    if not paths:
        return -1
    # Match the SQL's explicit textual tie breaker, including two-digit IDs.
    a = min(paths, key=lambda p: (p["cost"], "," + ",".join(map(str, p["route"])) + ","))
    return min((a["cost"] + b["cost"] for b in paths if compatible(a, b)), default=-1)


def make_database(path, nodes, edges):
    with sqlite3.connect(path) as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO nodes VALUES (?,?)", nodes)
        db.executemany("INSERT INTO edges VALUES (?,?,?)", edges)


def generated_graph(seed, require_greedy_error=True):
    rng = random.Random(f"witness-routes-v1:{seed}")
    for candidate in range(1000):
        # Two risk-disjoint backbone routes plus random forward edges.
        nodes = [(0, None), *[(i, i) for i in range(1, 7)],
                 (7, rng.randint(1, 6)), (8, rng.randint(1, 6)), (9, None)]
        backbone = {(0, 1), (1, 2), (2, 3), (3, 9),
                    (0, 4), (4, 5), (5, 6), (6, 9)}
        pairs = backbone | {(u, v) for u in range(9) for v in range(u+1, 10)
                            if rng.random() < 0.24}
        edges = [(u, v, rng.randint(1, 25)) for u, v in sorted(pairs)]
        if len(enumerate_paths(nodes, edges)) > 64:
            continue
        optimum = python_optimum(nodes, edges)
        greedy = python_greedy(nodes, edges)
        if not require_greedy_error or greedy != optimum:
            return nodes, edges, optimum, greedy, candidate
    raise ValueError("No graph met the outcome-blind reference qualification")


class RouteDatabase(Workspace):
    contract, schema, parameters = CONTRACT, SCHEMA, PARAMETERS
    claim = "The publisher's minimum_total_cost is the true optimum under the contract."

    def __init__(self, nodes, edges, image=IMAGE, source=0, sink=9):
        self.tmp = tempfile.TemporaryDirectory(prefix="witness-routes-")
        self.path = Path(self.tmp.name)
        self.path.chmod(0o755)
        self.image = image
        self.parameters = {"source": source, "sink": sink}
        self.expected = python_optimum(nodes, edges, source, sink)
        make_database(self.path / "records.sqlite", nodes, edges)
        with sqlite3.connect(self.path / "records.sqlite") as db:
            exact = db.execute(ORACLE_SQL, self.parameters).fetchone()[0]
        if exact != self.expected:
            self.close()
            raise ValueError("Independent route references disagree")
        (self.path / "README.md").write_text(CONTRACT)
        (self.path / "schema.sql").write_text(SCHEMA)

    def hashes(self):
        return {str(p.relative_to(self.path)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(self.path.rglob("*")) if p.is_file()}


class RouteWorkspace(RouteDatabase):
    def __init__(self, seed, truth, image=IMAGE):
        if type(truth) is not bool:
            raise ValueError("Truth must be boolean")
        nodes, edges, expected, greedy, self.candidate = generated_graph(seed)
        super().__init__(nodes, edges, image)
        with sqlite3.connect(self.path / "records.sqlite") as db:
            sql_greedy = db.execute(GREEDY_SQL, PARAMETERS).fetchone()[0]
        if sql_greedy != greedy or self.expected != expected:
            self.close()
            raise ValueError("Independent greedy route references disagree")
        self.inherited_query = ORACLE_SQL if truth else GREEDY_SQL
        self.inherited_execution = execute_query(self, self.inherited_query)
        published = scalar_result(self.inherited_execution)
        if published is None or (published == self.expected) != truth:
            self.close()
            raise ValueError("Route program does not realize planned label")
        self.report = {"source": 0, "sink": 9, "minimum_total_cost": published}
        (self.path / "report.json").write_text(json.dumps(self.report, indent=2) + "\n")
        (self.path / "publisher_query.sql").write_text(self.inherited_query)
        (self.path / "tests").mkdir()
        (self.path / "tests/test_smoke.py").write_text(
            "import sqlite3\n\ndef test_database_integrity():\n"
            "    with sqlite3.connect('file:records.sqlite?mode=ro', uri=True) as db:\n"
            "        assert db.execute('PRAGMA quick_check').fetchone() == ('ok',)\n")

def verify_generated(seeds, image=IMAGE):
    rows = []
    for seed in seeds:
        for truth in (False, True):
            workspace = RouteWorkspace(seed, truth, image)
            try:
                rows.append({"seed": seed, "truth": truth, "candidate": workspace.candidate,
                             "expected": workspace.expected, "report": workspace.report,
                             "execution": workspace.inherited_execution,
                             "source_sha256": workspace.hashes()})
            finally:
                workspace.close()
    return rows


def replay_worlds(seeds):
    """Fresh ordinary graphs plus predeclared boundary and relabeling conditions."""
    for seed in seeds:
        trap_nodes, trap_edges, *_ = generated_graph(seed, require_greedy_error=True)
        yield {"name": f"greedy-trap-{seed}", "nodes": trap_nodes, "edges": trap_edges}
        nodes, edges, *_ = generated_graph(seed, require_greedy_error=False)
        yield {"name": f"ordinary-{seed}", "nodes": nodes, "edges": edges}
        mapping = {0: 15, 9: 12, **dict(zip(range(1, 9), [7, 3, 10, 1, 8, 2, 11, 4],
                                         strict=True))}
        yield {"name": f"relabeled-{seed}",
               "nodes": [(mapping[n], g) for n, g in nodes],
               "edges": [(mapping[u], mapping[v], c) for u, v, c in edges],
               "source": 15, "sink": 12}
    nodes = [(0, None), (1, 1), (2, 1), (3, 2), (9, None)]
    cases = {
        "empty": [],
        "direct-only": [(0, 9, 3)],
        "shared-risk": [(0, 1, 1), (1, 9, 1), (0, 2, 1), (2, 9, 1)],
        "repeated-risk-within-route": [(0, 1, 1), (1, 2, 1), (2, 9, 1),
                                      (0, 3, 2), (3, 9, 2)],
        "direct-plus-other": [(0, 9, 1), (0, 1, 2), (1, 9, 2)],
        "cost-tie": [(0, 1, 1), (1, 9, 1), (0, 3, 1), (3, 9, 1)],
    }
    for name, edges in cases.items():
        yield {"name": name, "nodes": nodes, "edges": edges}
