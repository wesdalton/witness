"""Build the evidence-access corpus from real sandbox runs and run its free validity gates.

No model calls. Writes write-once outputs to --out and exits nonzero if any gate fails:
labels (two independent references per incident), identifiability (each family's
separating channels match the design and the report never separates a pair),
leakage (no label words in auditor-visible channels), timing, and baselines (the
identifiability-aware checker answers every incident under every access set exactly).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from witness.core.archive import write_once  # noqa: E402
from witness.evidence_access import baselines, corpus  # noqa: E402
from witness.evidence_access import execution as ex  # noqa: E402
from witness.evidence_access.tasks import all_tasks  # noqa: E402

LEAK = re.compile(r"\b(valid|invalid|honest|shadow|forged|truth|label|buggy|early_exit|"
                  r"dropped|timed_out_variant|within_limit)\b", re.I)


def sources() -> dict[str, str]:
    paths = [Path(__file__), *sorted((ROOT / "witness/evidence_access").rglob("*")),
             ROOT / "witness/core/sandbox.py"]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if p.is_file() and "__pycache__" not in p.parts}


def visible_text(incident: dict) -> str:
    channels = incident["channels"]
    return json.dumps({k: channels[k] for k in ("report", "manifest", "replay")})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261029)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit("Output directory must be new or empty")
    started = datetime.now(UTC).isoformat()
    rng = random.Random(args.seed)
    incidents, references = [], {}
    for task in all_tasks():
        built, meta = corpus.build_task(task, rng)
        incidents.extend(built)
        references.update(meta["references"])
        print(f"{task.name}: {len(built)} incidents", flush=True)
    rng.shuffle(incidents)

    labels = {i["id"]: {k: i[k] for k in ("task", "split", "family", "variant", "truth",
                                          "pair_group")} for i in incidents}
    checks = {i["id"]: corpus.label_checks(i, references[i["id"]]) for i in incidents}
    matrix = corpus.identifiability(incidents)
    separating = {g: {c for c in corpus.CHANNELS if row[c] == [True]}
                  for g, row in matrix.items()}
    design_ok = {g: (row["report"] == [False]
                     and separating[g] == corpus.DESIGN[g.split(":")[1]]
                     and all(row[c] in ([True], [False]) for c in corpus.CHANNELS))
                 for g, row in matrix.items()}
    leaks = {i["id"]: sorted(set(m.lower() for m in LEAK.findall(visible_text(i))))
             for i in incidents}
    leaks = {k: v for k, v in leaks.items() if v}
    table = baselines.score(incidents, separating)
    aware_exact = all(v["exact"] == 1.0 for k, v in table.items()
                      if k.startswith("aware_checker|"))
    gates = {
        "labels_two_references_agree": all(c["agree"] for c in checks.values()),
        "identifiability_matches_design": all(design_ok.values()),
        "no_label_words_in_visible_channels": not leaks,
        "aware_checker_exact_under_every_access_set": aware_exact,
        "incidents_per_task": len(incidents) // len(all_tasks()) == 8,
    }
    image = subprocess.run(["docker", "image", "inspect", ex.IMAGE, "--format", "{{.Id}}"],
                           capture_output=True, text=True).stdout.strip()
    args.out.mkdir(parents=True, exist_ok=True)
    write_once(args.out / "incidents.jsonl", "".join(
        json.dumps({"id": i["id"], "channels": i["channels"]}, sort_keys=True) + "\n"
        for i in incidents))
    write_once(args.out / "labels.json", labels)
    write_once(args.out / "references.json", {"references": references, "checks": checks})
    write_once(args.out / "gates.json", {
        "schema": "witness.evidence-access-gates.v1", "gates": gates,
        "passed": all(gates.values()), "identifiability": matrix,
        "separating_channels": {g: sorted(s) for g, s in separating.items()},
        "design": {k: sorted(v) for k, v in corpus.DESIGN.items()},
        "leaks": leaks, "baselines": table, "model_calls": 0})
    write_once(args.out / "manifest.json", {
        "schema": "witness.evidence-access-corpus.v1", "seed": args.seed,
        "started_at": started, "finished_at": datetime.now(UTC).isoformat(),
        "incidents": len(incidents), "image": ex.IMAGE, "image_id": image,
        "time_limit_s": ex.TIME_LIMIT_S, "python": platform.python_version(),
        "source_sha256": sources()})
    print(json.dumps(gates, indent=2))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
