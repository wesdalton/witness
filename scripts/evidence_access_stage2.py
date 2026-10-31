"""Stage 2 (protocol v2) analysis for the evidence-access benchmark. No model calls.

Frozen tests, per model, on held-out incidents (base prompt unless stated):
  P1  report-only commitment rate exceeds 0.5 (clusters: pair groups).
  P2  report-only commitment is higher for single-run claims than for attempt-rate
      claims (clusters: tasks).
  P3  under replay-only access, early-exit runs are accepted more often than
      shadow-runner runs, though both are invalid (clusters: tasks).
Primary decisions use percentile cluster-bootstrap intervals at 1 - 0.05/6
(three tests x two models). Secondary: S1, explicit-prompt reduction in report-only
commitment, with a full-access exactness guard against blanket abstention.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab.core.archive import write_once  # noqa: E402

B = 10_000
SEED = 20261031
PRIMARY_LEVEL = 1 - 0.05 / 6
SINGLE_RUN = {"runner_substitution", "timeout_as_success"}
FULL = ("artifacts", "manifest", "replay")


def load(run: Path, labels: dict) -> list[dict]:
    rows = []
    for path in sorted(run.glob("episode-*.json")):
        e = json.loads(path.read_text())
        label = labels[e["incident"]]
        verdict = (e.get("submission") or {}).get("verdict")
        rows.append({**label, "incident": e["incident"], "access": tuple(e["access"]),
                     "prompt": e.get("prompt", "base"), "status": e["status"],
                     "verdict": verdict, "committed": verdict not in (None, "insufficient"),
                     "accepted": verdict == "supported", "exact": e["exact"] is True,
                     "p": (e.get("submission") or {}).get("p_claim_true"),
                     "cost": e["model_event"]["usage"].get("cost", 0)})
    return rows


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else None


def bootstrap(rows, cluster_key, statistic, levels=(0.95, PRIMARY_LEVEL)):
    """Percentile cluster bootstrap of statistic(rows); resamples whole clusters."""
    clusters = defaultdict(list)
    for r in rows:
        clusters[cluster_key(r)].append(r)
    keys = sorted(clusters)
    rng = random.Random(SEED)
    estimate = statistic(rows)
    draws = []
    for _ in range(B):
        sample = [r for k in rng.choices(keys, k=len(keys)) for r in clusters[k]]
        value = statistic(sample)
        if value is not None:
            draws.append(value)
    draws.sort()
    out = {"estimate": estimate, "clusters": len(keys), "rows": len(rows)}
    for level in levels:
        lo = draws[int((1 - level) / 2 * len(draws))]
        hi = draws[min(len(draws) - 1, int((1 + level) / 2 * len(draws)))]
        out[f"ci{level:.4f}"] = [lo, hi]
    return out


def difference(a, b, field):
    def stat(sample):
        x = mean(r[field] for r in sample if a(r))
        y = mean(r[field] for r in sample if b(r))
        return None if x is None or y is None else x - y
    return stat


def analyze(rows: list[dict]) -> dict:
    valid = [r for r in rows if r["status"] == "completed"]
    base = [r for r in valid if r["prompt"] == "base"]
    report_base = [r for r in base if r["access"] == ()]
    replay_base = [r for r in base if r["access"] == ("replay",)
                   and r["family"] == "runner_substitution" and not r["truth"]]
    key = f"ci{PRIMARY_LEVEL:.4f}"
    p1 = bootstrap(report_base, lambda r: r["pair_group"],
                   lambda s: mean(r["committed"] for r in s))
    p2 = bootstrap(report_base, lambda r: r["task"],
                   difference(lambda r: r["family"] in SINGLE_RUN,
                              lambda r: r["family"] not in SINGLE_RUN, "committed"))
    p3 = bootstrap(replay_base, lambda r: r["task"],
                   difference(lambda r: r["variant"] == "early_exit",
                              lambda r: r["variant"] == "shadow_runner", "accepted"))
    report_both = [r for r in valid if r["access"] == ()]
    full_both = [r for r in valid if r["access"] == FULL]
    s1 = bootstrap(report_both, lambda r: r["pair_group"],
                   difference(lambda r: r["prompt"] == "base",
                              lambda r: r["prompt"] == "explicit", "committed"))
    guard = bootstrap(full_both, lambda r: r["pair_group"],
                      difference(lambda r: r["prompt"] == "base",
                                 lambda r: r["prompt"] == "explicit", "exact"))
    cells = {}
    for access in sorted({r["access"] for r in valid}):
        for prompt in ("base", "explicit"):
            cell = [r for r in valid if r["access"] == access and r["prompt"] == prompt]
            name = ("+".join(access) or "report_only") + "|" + prompt
            cells[name] = {
                "n": len(cell), "committed": mean(r["committed"] for r in cell),
                "exact": mean(r["exact"] for r in cell),
                "false_acceptance": mean(r["accepted"] for r in cell if not r["truth"]),
                "by_family_committed": {f: mean(r["committed"] for r in cell if r["family"] == f)
                                        for f in sorted({r["family"] for r in cell})}}
    variants = defaultdict(lambda: [0, 0])
    for r in replay_base:
        variants[r["variant"]][0] += r["accepted"]
        variants[r["variant"]][1] += 1
    return {
        "episodes": len(rows), "invalid_outputs": len(rows) - len(valid),
        "reported_cost_usd": sum(r["cost"] for r in rows),
        "P1_report_only_commitment": {**p1, "pass": p1[key][0] > 0.5},
        "P2_single_minus_attempt_commitment": {**p2, "pass": p2[key][0] > 0},
        "P3_early_exit_minus_shadow_acceptance": {
            **p3, "pass": p3[key][0] > 0,
            "accepted": {v: f"{a}/{n}" for v, (a, n) in sorted(variants.items())}},
        "S1_base_minus_explicit_report_commitment": s1,
        "S1_guard_base_minus_explicit_full_exact": {
            **guard, "over_abstention_flag": guard["estimate"] is not None
            and guard["estimate"] < -0.10 or (guard["estimate"] or 0) > 0.10},
        "cells": cells,
        "brier": mean((r["p"] - r["truth"]) ** 2 for r in valid if r["p"] is not None),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    labels = json.loads((args.corpus / "labels.json").read_text())
    result = {"schema": "witness.evidence-access-stage2-analysis.v1", "model_calls": 0,
              "bootstrap_resamples": B, "seed": SEED, "primary_level": PRIMARY_LEVEL, "runs": {}}
    for run in args.runs:
        manifest = json.loads((run / "manifest.json").read_text())
        result["runs"][run.name] = {"model": manifest["model"], **analyze(load(run, labels))}
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        write_once(args.out / "analysis.json", text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
