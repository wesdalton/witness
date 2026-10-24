"""Free deterministic deduplication ablation of the four completed schedule programs."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from measure_query_work import measure  # noqa: E402
from swarm_lab.schedule_cases import ScheduleDatabase, replay_worlds  # noqa: E402


def main():
    batch = ROOT / "research/portfolio/luna-schedule-calibration-01"
    manifest = json.loads((batch / "manifest.json").read_text())
    previous = json.loads((ROOT / "research/portfolio/query-work-measurement-v1.json").read_text())
    baselines = {row["episode"]: row for row in previous["rows"]
                 if row["batch"] == batch.name and row["condition"].startswith("boundary")}
    rows = []
    for path in sorted(batch.glob("episode-*.json")):
        record = json.loads(path.read_text())
        original = record["submission"]["audit_sql"]
        if len(re.findall(r"\bUNION\s+ALL\b", original, flags=re.I)) != 1:
            raise ValueError("Expected the manually reviewed single recursive UNION ALL")
        changed = re.sub(r"\bUNION\s+ALL\b", "UNION", original, count=1, flags=re.I)
        worlds = []
        for spec in replay_worlds(range(22001, 22005)):
            workspace = ScheduleDatabase(
                spec["workers"], spec["operations"], spec["ordering"],
                spec["initial"], manifest["image"])
            try:
                result = measure(workspace, changed)
                if result["aggregate"] != workspace.expected:
                    raise ValueError("Deduplication changed a replay result")
                worlds.append({"name": spec["name"], "expected": workspace.expected,
                               "measurement": result, "workspace_sha256": workspace.hashes()})
            finally:
                workspace.close()
        baseline = baselines[path.name]
        measured = next(row for row in worlds if row["name"] == baseline["condition"])
        before, after = (baseline["verification"]["nominal_progress_units"],
                         measured["measurement"]["nominal_progress_units"])
        if measured["measurement"]["sqlite_version"] != baseline["verification"]["sqlite_version"]:
            raise ValueError("SQLite versions differ across measurements")
        rows.append({"episode": path.name,
                     "episode_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "original_sql_sha256": hashlib.sha256(original.encode()).hexdigest(),
                     "modified_sql": changed, "worlds": worlds,
                     "all_replay_results_correct": True,
                     "boundary_before_nominal_units": before,
                     "boundary_after_nominal_units": after,
                     "boundary_ratio_before_over_after": before/after})
        print(json.dumps({k: v for k, v in rows[-1].items()
                          if k not in ("worlds", "modified_sql")}), flush=True)
    result = {
        "model_inference": False,
        "analysis_timing": "Post-hoc, after the complete capability pilot and finite replay",
        "intervention": "Replace the sole recursive UNION ALL with UNION; nothing else",
        "scope": "The four reviewed programs carry the complete future-relevant state, and "
        "MIN over terminal balances is invariant to duplicate paths reaching that same state. "
        "This argument does not apply to counting schedules, path-dependent states or arbitrary SQL.",
        "measurement": "SQLite progress callbacks times 1000: approximate work, not time or cost.",
        "historical_artifacts_unchanged": True, "rows": rows,
        "implementation_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), ROOT / "scripts/measure_query_work.py",
                      ROOT / "swarm_lab/schedule_cases.py")}}
    with (ROOT / "research/portfolio/query-efficiency-analysis.json").open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
