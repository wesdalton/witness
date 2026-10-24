"""Post-hoc isolated VM-work measurement; no agent inference or historical trace edits."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab.reconciliation_query import DRIVER, scalar_result  # noqa: E402
from swarm_lab.route_cases import ORACLE_SQL as ROUTE_ORACLE_SQL  # noqa: E402
from swarm_lab.route_cases import RouteWorkspace  # noqa: E402
from swarm_lab.schedule_cases import ORACLE_SQL as SCHEDULE_ORACLE_SQL  # noqa: E402
from swarm_lab.schedule_cases import (  # noqa: E402
    ScheduleDatabase,
    ScheduleWorkspace,
    replay_worlds,
)

MEASURED_DRIVER = DRIVER.replace(
    '"rows": rows[:100], "rows_truncated": len(rows) > 100}',
    '"rows": rows[:100], "rows_truncated": len(rows) > 100, '
    '"progress_callbacks": steps[0]//1000, "nominal_progress_units": steps[0], '
    '"sqlite_version": sqlite3.sqlite_version}')
if MEASURED_DRIVER == DRIVER:
    raise ValueError("Instrumentation marker changed")


def measure(workspace, sql):
    payload = json.dumps({"sql": sql, "parameters": workspace.parameters})
    result = workspace.execute(
        ["python", "-"], "REQUEST_JSON = " + repr(payload) + "\n" + MEASURED_DRIVER)
    if result["exit_code"] or result["timed_out"] or result["output_truncated"]:
        raise ValueError("Measurement did not finish under the original resource limit")
    value = json.loads(result["stdout"])
    return {"progress_callbacks": value["progress_callbacks"],
            "nominal_progress_units": value["nominal_progress_units"],
            "sqlite_version": value["sqlite_version"],
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
            oracle_sql = (SCHEDULE_ORACLE_SQL if spec["task"] == "schedules"
                          else ROUTE_ORACLE_SQL)
            try:
                if workspace.hashes()["records.sqlite"] != record["workspace_sha256"][
                        "records.sqlite"]:
                    raise ValueError("Reconstructed observed database differs")
                baseline = measure(workspace, "SELECT 1")
                actual = measure(workspace, sql)
                oracle = measure(workspace, oracle_sql)
                if (actual["aggregate"] != workspace.expected
                        or oracle["aggregate"] != workspace.expected):
                    raise ValueError("Instrumented verifier changed its finite result")
                rows.append({"batch": name, "episode": path.name, "condition": "observed",
                             "episode_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                             "expected": workspace.expected, "baseline": baseline,
                             "verification": actual, "reference": oracle})
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
                             "verification": actual,
                             "reference": measure(workspace, oracle_sql)})
            finally:
                workspace.close()
    result = {
        "model_inference": False, "analysis_timing": "Post-hoc after both fixed pilots completed",
        "driver_sha256": hashlib.sha256(MEASURED_DRIVER.encode()).hexdigest(),
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (Path(__file__), ROOT / "swarm_lab/reconciliation_query.py",
                                    ROOT / "swarm_lab/route_cases.py",
                                    ROOT / "swarm_lab/schedule_cases.py")},
        "interpretation": "Each SQL statement costs one query credit. Progress callbacks are an "
        "approximate SQLite-version-dependent work measure, not rigorous instruction bounds. "
        "They can include preparation work. Nominal units = callbacks*1000; not API dollars, "
        "human effort, model reasoning tokens or a causal treatment outcome.",
        "rows": rows}
    target = ROOT / "research/portfolio/query-work-measurement-v1.json"
    with target.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"queries_measured": 3*len(rows), "rows": len(rows),
                      "verifier_nominal_units": [
                          r["verification"]["nominal_progress_units"] for r in rows],
                      "reference_nominal_units": [
                          r["reference"]["nominal_progress_units"] for r in rows]}))


if __name__ == "__main__":
    main()
