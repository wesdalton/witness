"""Free exact-label, numeric-domain and initial-view gates before scarce-query inference."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from swarm_lab.legacy.portfolio_cases import IMAGE  # noqa: E402
from swarm_lab.legacy.query_study import initial_view  # noqa: E402
from swarm_lab.legacy.reconciliation_query import execute_query, scalar_result  # noqa: E402
from swarm_lab.legacy.route_cases import (  # noqa: E402
    CONTRACT_REVISION,
    ORACLE_SQL,
    RouteDatabase,
    RouteWorkspace,
    replay_worlds,
)


def audit():
    image = subprocess.check_output(
        ["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], text=True).strip()
    cases, equality, replay = [], [], []
    for seed in range(18001, 18005):
        views = []
        for truth in (False, True):
            workspace = RouteWorkspace(seed, truth, image, "same_program")
            try:
                smoke = workspace.execute(["python", "-m", "pytest", "-q", "tests/test_smoke.py"])
                if smoke["exit_code"] or smoke["timed_out"] or smoke["output_truncated"]:
                    raise ValueError("Integrity gate failed")
                views.append(initial_view(workspace, "no_peers", smoke, "program", 1))
                result = execute_query(workspace, ORACLE_SQL)
                if scalar_result(result) != workspace.expected:
                    raise ValueError("Live independent reference mismatch")
                cases.append({"seed": seed, "truth": truth, "expected": workspace.expected,
                              "report": workspace.report, "oracle_execution": result,
                              "publisher_execution": workspace.inherited_execution,
                              "workspace_sha256": workspace.hashes()})
            finally:
                workspace.close()
        if views[0] != views[1]:
            raise ValueError("Initial view reveals truth")
        equality.append({"seed": seed, "identical_initial_views": True,
                         "view_sha256": hashlib.sha256(
                             json.dumps(views[0], sort_keys=True).encode()).hexdigest()})
    for spec in replay_worlds(range(19001, 19009)):
        workspace = RouteDatabase(spec["nodes"], spec["edges"], image,
                                  spec.get("source", 0), spec.get("sink", 9))
        try:
            result = execute_query(workspace, ORACLE_SQL)
            if scalar_result(result) != workspace.expected:
                raise ValueError("Fresh replay reference mismatch")
            replay.append({"name": spec["name"], "expected": workspace.expected,
                           "execution": result, "workspace_sha256": workspace.hashes()})
        finally:
            workspace.close()
    return {"model_inference": False, "contract_revision": CONTRACT_REVISION,
            "image": image, "cases": cases, "initial_view_equality": equality,
            "replay_reference_gate": replay,
            "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (Path(__file__), ROOT / "swarm_lab/legacy/route_cases.py",
                                        ROOT / "swarm_lab/legacy/query_study.py")}}


if __name__ == "__main__":
    target = ROOT / "research/portfolio/scarce-query-reference-gate-v1.json"
    if target.exists():
        raise FileExistsError(target)
    result = audit()
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"cases": len(result["cases"]), "equal_pairs": 4,
                      "replay_conditions": len(result["replay_reference_gate"])}))
