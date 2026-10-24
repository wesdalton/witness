"""Free three-reference, receipt, equality, mutation and execution gates."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab import schedule_cases as cases  # noqa: E402
from swarm_lab.portfolio_cases import IMAGE  # noqa: E402
from swarm_lab.query_study import initial_view  # noqa: E402
from swarm_lab.reconciliation_query import execute_query, scalar_result  # noqa: E402


def audit():
    image = subprocess.check_output(
        ["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], text=True).strip()
    sql = cases.ORACLE_SQL
    register = ("CASE o.worker WHEN 0 THEN s.r0 WHEN 1 THEN s.r1\n"
                "                        WHEN 2 THEN s.r2 ELSE s.r3 END")
    mutants = {
        "atomic-increment": sql.replace(register + " + o.delta", "s.balance + o.delta"),
        "maximum-outcome": sql.replace("MIN(balance)", "MAX(balance)"),
        "ignore-cross-worker-order": sql.replace(
            "WHERE d.after_op=o.op",
            "WHERE d.after_op=o.op AND d.before_op IN "
            "(SELECT p.op FROM operations p WHERE p.worker=o.worker)"),
        "absolute-delta": sql.replace("END + o.delta", "END + ABS(o.delta)"),
        "single-register": sql.replace(register, "s.r0"),
        "initial-zero": sql.replace("SELECT 0, :initial_balance", "SELECT 0, 0"),
        "include-partial-schedules": sql.replace(
            "WHERE done=(SELECT SUM(1 << op) FROM operations)", ""),
    }
    if any(value == sql for value in mutants.values()):
        raise ValueError("A mutation did not change SQL")
    rejected = {name: [] for name in mutants}
    worlds = []
    for spec in cases.replay_worlds(range(22001, 22005)):
        args = [spec[k] for k in ("workers", "operations", "ordering", "initial")]
        permutations = cases.permutation_outcomes(*args)
        if permutations != cases.explore_outcomes(*args):
            raise ValueError("Independent permutation/state references disagree")
        workspace = cases.ScheduleDatabase(*args, image=image)
        try:
            result = execute_query(workspace, sql)
            if scalar_result(result) != min(permutations):
                raise ValueError("Live SQL reference fails semantic or resource bounds")
            with sqlite3.connect(workspace.path / "records.sqlite") as db:
                for name, mutant in mutants.items():
                    actual = db.execute(mutant, workspace.parameters).fetchone()[0]
                    if actual != workspace.expected:
                        rejected[name].append({"name": spec["name"], "actual": actual,
                                               "expected": workspace.expected})
            worlds.append({"name": spec["name"], "expected": workspace.expected,
                           "outcomes": sorted(permutations), "execution": result,
                           "workspace_sha256": workspace.hashes()})
        finally:
            workspace.close()
    planned, equality = [], []
    for seed in (21001, 21002):
        views = []
        for truth in (False, True):
            workspace = cases.ScheduleWorkspace(seed, truth, image)
            try:
                smoke = workspace.execute(["python", "-m", "pytest", "-q", "tests/test_smoke.py"])
                if smoke["exit_code"] or smoke["timed_out"] or smoke["output_truncated"]:
                    raise ValueError("Initial integrity gate failed")
                views.append(initial_view(workspace, "no_peers", smoke, "program"))
                result = execute_query(workspace, sql)
                if scalar_result(result) != workspace.expected:
                    raise ValueError("Planned live reference mismatch")
                planned.append({"seed": seed, "truth": truth, "expected": workspace.expected,
                                "publisher_execution": workspace.publisher_execution,
                                "report": workspace.report, "reference_execution": result,
                                "workspace_sha256": workspace.hashes()})
            finally:
                workspace.close()
        if views[0] != views[1]:
            raise ValueError("Full initial view reveals finite truth")
        equality.append({"seed": seed, "identical_initial_views": True})
    return {"model_inference": False, "image": image, "planned": planned, "worlds": worlds,
            "view_equality": equality, "mutation_counterexamples": rejected,
            "passed": all(rejected.values()), "source_sha256": {
                str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (Path(__file__), ROOT / "swarm_lab/schedule_cases.py",
                          ROOT / "swarm_lab/query_study.py")}}


if __name__ == "__main__":
    target = ROOT / "research/portfolio/schedule-reference-gate-v1.json"
    if target.exists():
        raise FileExistsError(target)
    result = audit()
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"planned": len(result["planned"]), "worlds": len(result["worlds"]),
                      "mutations_caught": sum(bool(v) for v in
                                              result["mutation_counterexamples"].values()),
                      "passed": result["passed"]}))
    raise SystemExit(not result["passed"])
