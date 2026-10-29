"""Free semantic/mutation/execution gates for the route task."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from swarm_lab.legacy.portfolio_cases import IMAGE  # noqa: E402
from swarm_lab.legacy.reconciliation_query import execute_query, scalar_result  # noqa: E402
from swarm_lab.legacy.route_cases import (  # noqa: E402
    GREEDY_SQL,
    ORACLE_SQL,
    PATHS_SQL,
    RouteDatabase,
    replay_worlds,
    verify_generated,
)


def audit(image):
    mutants = {
        "greedy-first": GREEDY_SQL,
        "risk-ignored": ORACLE_SQL.replace("AND (a.risks & b.risks) = 0", ""),
        "allow-identical-path": ORACLE_SQL.replace("a.route < b.route", "a.route <= b.route"),
        "return-zero-infeasible": ORACLE_SQL.replace(", -1)", ", 0)"),
        "maximum-pair": ORACLE_SQL.replace("MIN(a.cost + b.cost)", "MAX(a.cost + b.cost)"),
        "minimum-single": PATHS_SQL + "SELECT COALESCE(MIN(cost),-1) FROM complete",
        "average-pair": ORACLE_SQL.replace("a.cost + b.cost", "(a.cost + b.cost)/2"),
        "only-increasing-node-ids": ORACLE_SQL.replace(
            "WHERE p.node != :sink", "WHERE p.node != :sink AND e.u < e.v"),
        "hardcoded-endpoints": ORACLE_SQL.replace(":source", "0").replace(":sink", "9"),
    }
    rejected = {name: [] for name in mutants}
    worlds = []
    for spec in replay_worlds(range(15001, 15009)):
        workspace = RouteDatabase(spec["nodes"], spec["edges"], image,
                                  spec.get("source", 0), spec.get("sink", 9))
        try:
            result = execute_query(workspace, ORACLE_SQL)
            if scalar_result(result) != workspace.expected:
                raise ValueError("Live reference fails correctness or execution limits")
            with sqlite3.connect(workspace.path / "records.sqlite") as db:
                for name, sql in mutants.items():
                    value = db.execute(sql, workspace.parameters).fetchone()[0]
                    if value != workspace.expected:
                        rejected[name].append(spec["name"])
            worlds.append({"name": spec["name"], "expected": workspace.expected,
                           "parameters": workspace.parameters, "execution": result,
                           "workspace_sha256": workspace.hashes()})
        finally:
            workspace.close()
    if any(not evidence for evidence in rejected.values()):
        raise ValueError("A proposed semantic mutation lacks a discriminating condition")
    return {"schema": "witness.route-reference-gate.v1", "model_inference": False,
            "image": image, "worlds": worlds, "mutation_counterexamples": rejected,
            "planned_cases": verify_generated(range(14001, 14005), image),
            "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (Path(__file__), ROOT / "swarm_lab/legacy/route_cases.py",
                                        ROOT / "swarm_lab/legacy/reconciliation_query.py")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    image = subprocess.check_output(
        ["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], text=True).strip()
    result = audit(image)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"worlds": len(result["worlds"]),
                      "planned_cases": len(result["planned_cases"]),
                      "detected_mutants": len(result["mutation_counterexamples"])}))


if __name__ == "__main__":
    main()
