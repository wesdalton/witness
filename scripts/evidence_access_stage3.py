"""Protocol v3 analysis for the evidence-access benchmark. No model calls.

Primary family (decided at 1 - 0.05/11, percentile cluster bootstrap):
  R1  for each of the three new model families, P1 (base report-only commitment > 0.5,
      clusters: pair groups) and P3 (base replay-only acceptance, early exit minus
      shadow runner > 0, clusters: tasks). Six tests.
  I1  for each of the five models, the observed-counts arm lowers early-exit acceptance
      under replay-only access (base minus counts > 0, clusters: tasks). Five tests.
Descriptive: noticed-but-accepted rate, counts-arm guards, and full-access exactness on
the repaired attempt-rate family.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from witness.core.archive import write_once  # noqa: E402

_spec = importlib.util.spec_from_file_location("stage2", ROOT / "scripts/evidence_access_stage2.py")
s2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s2)

NEW_FAMILIES = {"anthropic/claude-sonnet-5.5", "google/gemini-3.8-flash",
                "deepseek/deepseek-v4.1-flash"}
PRIMARY_LEVEL = 1 - 0.05 / 11
LEVELS = (0.95, PRIMARY_LEVEL)


def load(run: Path, labels: dict) -> list[dict]:
    rows = s2.load(run, labels)
    episodes = [json.loads(p.read_text()) for p in sorted(run.glob("episode-*.json"))]
    for row, e in zip(rows, episodes, strict=True):
        counts = (e.get("submission") or {}).get("observed_counts") or []
        replay = [c for c in counts if c["channel"] == "replay"]
        row["episode"] = e["episode"]
        row["replay_counts_null"] = bool(replay) and all(
            c["passed"] is None and c["failed"] is None for c in replay)
    return rows


def boot(rows, key, stat):
    return s2.bootstrap(rows, key, stat, LEVELS)


def analyze(rows: list[dict], model: str) -> dict:
    valid = [r for r in rows if r["status"] == "completed"]
    tag = f"ci{PRIMARY_LEVEL:.4f}"
    replay = [r for r in valid if r["access"] == ("replay",)
              and r["family"] == "runner_substitution"]
    base = [r for r in valid if r["prompt"] == "base"]
    report_base = [r for r in base if r["access"] == ()]
    replay_base_invalid = [r for r in replay if r["prompt"] == "base" and not r["truth"]]
    early = [r for r in replay if r["variant"] == "early_exit"]
    out = {"model": model, "episodes": len(rows), "invalid_outputs": len(rows) - len(valid),
           "reported_cost_usd": sum(r["cost"] for r in rows), "primary": {}}

    def primary(name, result, threshold):
        result["pass"] = result[tag][0] > threshold
        out["primary"][name] = result

    p1 = boot(report_base, lambda r: r["pair_group"], lambda s: s2.mean(r["committed"] for r in s))
    p3 = boot(replay_base_invalid, lambda r: r["task"],
              s2.difference(lambda r: r["variant"] == "early_exit",
                            lambda r: r["variant"] == "shadow_runner", "accepted"))
    i1 = boot(early, lambda r: r["task"],
              s2.difference(lambda r: r["prompt"] == "base",
                            lambda r: r["prompt"] == "counts", "accepted"))
    if model in NEW_FAMILIES:
        primary("R1_P1_report_only_commitment", p1, 0.5)
        primary("R1_P3_early_minus_shadow_acceptance", p3, 0.0)
    else:
        out["replication_descriptive"] = {"P1": p1, "P3": p3}
    primary("I1_base_minus_counts_early_exit_acceptance", i1, 0.0)
    i1["practically_meaningful"] = i1["pass"] and i1["estimate"] >= 0.20

    def rate(cell, field="accepted"):
        return {"k": sum(r[field] for r in cell), "n": len(cell)}

    counts_early = [r for r in early if r["prompt"] == "counts"]
    out["descriptive"] = {
        "early_exit_accepted": {arm: rate([r for r in early if r["prompt"] == arm])
                                for arm in ("base", "counts")},
        "shadow_accepted": {arm: rate([r for r in replay if r["variant"] == "shadow_runner"
                                       and r["prompt"] == arm]) for arm in ("base", "counts")},
        "honest_replay_accepted": {arm: rate([r for r in replay if r["variant"] == "honest"
                                              and r["prompt"] == arm])
                                   for arm in ("base", "counts")},
        "counts_early_exit_replay_recorded_null": rate(counts_early, "replay_counts_null"),
        "noticed_but_accepted": {"k": sum(r["replay_counts_null"] and r["accepted"]
                                          for r in counts_early),
                                 "n": sum(r["replay_counts_null"] for r in counts_early)},
        "report_only_committed": {arm: rate([r for r in valid if r["access"] == ()
                                             and r["prompt"] == arm], "committed")
                                  for arm in ("base", "counts")},
        "full_access_exact": {arm: rate([r for r in valid if r["access"] == s2.FULL
                                         and r["prompt"] == arm], "exact")
                              for arm in ("base", "counts")},
        "repaired_attempt_family_full_exact_base": {
            v: rate([r for r in base if r["access"] == s2.FULL and r["variant"] == v], "exact")
            for v in ("all_reported", "declared_exclusion", "dropped_failures")},
        "brier": s2.mean((r["p"] - r["truth"]) ** 2 for r in valid if r["p"] is not None),
    }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    labels = json.loads((args.corpus / "labels.json").read_text())
    result = {"schema": "witness.evidence-access-stage3-analysis.v1", "model_calls": 0,
              "bootstrap_resamples": s2.B, "seed": s2.SEED, "primary_level": PRIMARY_LEVEL,
              "runs": {}}
    by_model: dict[str, tuple[list[str], list[dict]]] = {}
    for run in args.runs:
        model = json.loads((run / "manifest.json").read_text())["model"]
        names, rows = by_model.setdefault(model, ([], []))
        names.append(run.name)
        rows.extend(load(run, labels))
    for model, (names, rows) in by_model.items():
        if len({r["episode"] for r in rows}) != len(rows):
            raise ValueError(f"{model}: duplicate episodes across continuation runs")
        result["runs"][model] = {"run_dirs": names, **analyze(rows, model)}
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        write_once(args.out / "analysis.json", text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
