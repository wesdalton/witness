"""Post-hoc isolated VM-work measurement; no agent inference or historical trace edits."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab.reconciliation_query import DRIVER, scalar_result  # noqa: E402
from swarm_lab.route_cases import RouteWorkspace  # noqa: E402
from swarm_lab.schedule_cases import (  # noqa: E402
    ScheduleDatabase,
    ScheduleWorkspace,
    replay_worlds,
)

MEASURED_DRIVER = DRIVER.replace(
    '"rows": rows[:100], "rows_truncated": len(rows) > 100}',
    '"rows": rows[:100], "rows_truncated": len(rows) > 100, '
    '"vm_steps_lower_bound": steps[0], "vm_steps_upper_exclusive": steps[0]+1000}')
if MEASURED_DRIVER == DRIVER:
    raise ValueError("Instrumentation marker changed")


def measure(workspace, sql):
    payload = json.dumps({"sql": sql, "parameters": workspace.parameters})
    result = workspace.execute(
        ["python", "-"], "REQUEST_JSON = " + repr(payload) + "\n" + MEASURED_DRIVER)
    if result["exit_code"] or result["timed_out"] or result["output_truncated"]:
        raise ValueError("Measurement did not finish under the original resource limit")
    value = json.loads(result["stdout"])
    return {"vm_steps_lower_bound": value["vm_steps_lower_bound"],
            "vm_steps_upper_exclusive": value["vm_steps_upper_exclusive"],
            "aggregate": scalar_result(result), "execution": result}


def main():
    rows = []
    for name in ("luna-scarce-query-calibration-01", "luna-schedule-calibration-01"):
        batch = ROOT / "research/portfolio" / name
        manifest = json.loads((batch / "manifest.json").read_text())
        for path in sorted(batch.glob("episode-*.json")):
            record = json.loads(path.read_text())
            spec = record["spec"]
            workspace = (ScheduleWorkspace(spec["seed"], spec["truth"], manifest["image"])
                         if spec["task"] == "schedules" else RouteWorkspace(
                             spec["seed"], spec["truth"], manifest["image"], "same_program"))
            sql = record["submission"]["audit_sql"]
            try:
                if workspace.hashes()["records.sqlite"] != record["workspace_sha256"][
                        "records.sqlite"]:
                    raise ValueError("Reconstructed observed database differs")
                baseline = measure(workspace, "SELECT 1")
                actual = measure(workspace, sql)
                if actual["aggregate"] != workspace.expected:
                    raise ValueError("Instrumented verifier changed its finite result")
                rows.append({"batch": name, "episode": path.name, "condition": "observed",
                             "episode_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                             "expected": workspace.expected, "baseline": baseline,
                             "verification": actual})
            finally:
                workspace.close()
            if spec["task"] != "schedules":
                continue
            # Predeclared replay boundary: four zero-delta workers, no cross-worker edges.
            boundary = next(w for w in replay_worlds([])
                            if len(w["workers"]) == 4 and all(d == 0 for _, d in w["workers"]))
            workspace = ScheduleDatabase(
                boundary["workers"], boundary["operations"], boundary["ordering"],
                boundary["initial"], manifest["image"])
            try:
                actual = measure(workspace, sql)
                if actual["aggregate"] != workspace.expected:
                    raise ValueError("Instrumented boundary result differs")
                rows.append({"batch": name, "episode": path.name, "condition": boundary["name"],
                             "expected": workspace.expected,
                             "baseline": measure(workspace, "SELECT 1"),
                             "verification": actual})
            finally:
                workspace.close()
    result = {
        "model_inference": False, "analysis_timing": "Post-hoc after both fixed pilots completed",
        "driver_sha256": hashlib.sha256(MEASURED_DRIVER.encode()).hexdigest(),
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (Path(__file__), ROOT / "swarm_lab/reconciliation_query.py",
                                    ROOT / "swarm_lab/route_cases.py",
                                    ROOT / "swarm_lab/schedule_cases.py")},
        "interpretation": "Each SQL statement costs one query credit. VM work is SQLite-version "
        "dependent and measured in 1000-instruction intervals; it is not API dollars, "
        "human effort, model reasoning tokens or a causal treatment outcome.",
        "rows": rows}
    target = ROOT / "research/portfolio/query-work-measurement.json"
    with target.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"queries_measured": 2*len(rows), "rows": len(rows),
                      "verifier_vm_step_lower_bounds": [
                          r["verification"]["vm_steps_lower_bound"] for r in rows]}))


if __name__ == "__main__":
    main()
