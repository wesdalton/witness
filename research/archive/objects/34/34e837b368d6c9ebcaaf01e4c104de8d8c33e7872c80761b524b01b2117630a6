"""Replay unchanged submitted SQL on fresh generated databases; no model inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab.reconciliation_cases import ReconciliationWorkspace  # noqa: E402
from swarm_lab.reconciliation_query import execute_query, scalar_result  # noqa: E402
from swarm_lab.route_cases import RouteDatabase, replay_worlds  # noqa: E402


def replay(episode_path, seeds):
    episode = json.loads(episode_path.read_text())
    manifest = json.loads((episode_path.parent / "manifest.json").read_text())
    if not episode["submission"] or "audit_sql" not in episode["submission"]:
        raise ValueError("No submitted artifact; do not impute one")
    if episode["spec"]["seed"] in seeds:
        raise ValueError("Replay worlds must differ from the observed database")
    sql = episode["submission"]["audit_sql"]
    rows = []
    if episode["spec"].get("task") == "routes":
        for spec in replay_worlds(seeds):
            workspace = RouteDatabase(spec["nodes"], spec["edges"], manifest["image"],
                                      spec.get("source", 0), spec.get("sink", 9))
            try:
                result = execute_query(workspace, sql)
                value = scalar_result(result)
                rows.append({"name": spec["name"], "parameters": workspace.parameters,
                             "expected": workspace.expected, "aggregate": value,
                             "correct": value == workspace.expected, "result": result,
                             "workspace_sha256": workspace.hashes()})
            finally:
                workspace.close()
        return replay_record(episode_path, manifest, sql, rows, 1)
    for seed in seeds:
        for truth in (False, True):
            workspace = ReconciliationWorkspace(seed, truth, manifest["image"], revision=2)
            try:
                result = execute_query(workspace, sql)
                value = scalar_result(result)
                rows.append({"seed": seed, "truth": truth, "expected": workspace.expected,
                             "aggregate": value, "correct": value == workspace.expected,
                             "result": result, "workspace_sha256": workspace.hashes()})
            finally:
                workspace.close()
    return replay_record(episode_path, manifest, sql, rows, 2)


def replay_record(episode_path, manifest, sql, rows, revision):
    return {"schema": "witness.query-replay.v1", "episode": str(episode_path),
            "episode_sha256": hashlib.sha256(episode_path.read_bytes()).hexdigest(),
            "audit_sql_sha256": hashlib.sha256(sql.encode()).hexdigest(),
            "image": manifest["image"], "generator_revision": revision,
            "implementation_sha256": {str(p.relative_to(ROOT)):
                                      hashlib.sha256(p.read_bytes()).hexdigest() for p in (
                                          Path(__file__), ROOT/"swarm_lab/reconciliation_cases.py",
                                          ROOT/"swarm_lab/reconciliation_query.py",
                                          ROOT/"swarm_lab/route_cases.py")},
            "worlds": rows, "correct_worlds": sum(r["correct"] for r in rows),
            "all_worlds_correct": all(r["correct"] for r in rows),
            "interpretation": "One generated agent query is one artifact. Replayed databases "
            "are test conditions, not independent model trials. No query repair or feedback."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(9001, 9009)))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.episode.resolve(), args.seeds)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"worlds": len(result["worlds"]),
                      "correct_worlds": result["correct_worlds"]}))


if __name__ == "__main__":
    main()
