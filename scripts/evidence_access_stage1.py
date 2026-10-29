"""Stage 1 calibration analysis for the evidence-access benchmark. No model calls.

Computes, per model: exact-answer rates, commitment when the granted evidence cannot
separate the pair, false acceptance, Brier loss of the stated probability, the H1
paired discordance (report-only vs a non-separating channel), the intraclass
correlation of commitment across pair groups, and the frozen sample-size rule.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab.core.archive import write_once  # noqa: E402

H1_CELLS = {"runner_substitution": [["manifest"]],
            "dropped_attempts": [["artifacts"], ["replay"], ["artifacts", "replay"]]}
DELTA, Z_ALPHA, Z_BETA = 0.15, 1.959964, 0.841621


def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k + 1))


def clopper_pearson(k, n, level):
    """Two-sided Clopper-Pearson interval by bisection."""
    tail = (1 - level) / 2

    def solve(f):
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) else (lo, mid)
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else solve(lambda p: 1 - binom_cdf(k - 1, n, p) < tail)
    upper = 1.0 if k == n else solve(lambda p: binom_cdf(k, n, p) > tail)
    return lower, upper


def rate(rows, key):
    rows = list(rows)
    k = sum(1 for r in rows if key(r))
    lo, hi = clopper_pearson(k, len(rows), 0.95) if rows else (None, None)
    return {"k": k, "n": len(rows), "rate": k / len(rows) if rows else None,
            "ci95": [lo, hi]}


def icc(groups):
    """One-way ANOVA ICC for a binary outcome grouped by cluster."""
    groups = [g for g in groups if g]
    if len(groups) < 2:
        return None, None
    n = sum(len(g) for g in groups)
    k = len(groups)
    grand = sum(sum(g) for g in groups) / n
    msb = sum(len(g) * (sum(g) / len(g) - grand) ** 2 for g in groups) / (k - 1)
    msw = sum(sum((x - sum(g) / len(g)) ** 2 for x in g) for g in groups) / max(1, n - k)
    m = (n - sum(len(g) ** 2 for g in groups) / n) / (k - 1)
    value = (msb - msw) / (msb + (m - 1) * msw) if msb + (m - 1) * msw > 0 else 0.0
    return max(0.0, value), n / k


def analyze(run: Path, labels: dict) -> dict:
    episodes = [json.loads(p.read_text()) for p in sorted(run.glob("episode-*.json"))]
    rows = []
    for e in episodes:
        label = labels[e["incident"]]
        sub = e.get("submission") or {}
        rows.append({**label, "incident": e["incident"], "access": tuple(e["access"]),
                     "status": e["status"], "expected": e["expected"],
                     "verdict": sub.get("verdict"), "p": sub.get("p_claim_true"),
                     "exact": e["exact"] is True,
                     "cost": e["model_event"]["usage"].get("cost", 0)})
    valid = [r for r in rows if r["status"] == "completed"]
    unidentified = [r for r in valid if r["expected"] == "insufficient"]
    identified = [r for r in valid if r["expected"] != "insufficient"]
    committed = lambda r: r["verdict"] != "insufficient"  # noqa: E731
    out = {
        "episodes": len(rows), "invalid_outputs": len(rows) - len(valid),
        "reported_cost_usd": sum(r["cost"] for r in rows),
        "exact": rate(valid, lambda r: r["exact"]),
        "commit_when_unidentified": rate(unidentified, committed),
        "false_acceptance": rate([r for r in valid if not r["truth"]],
                                 lambda r: r["verdict"] == "supported"),
        "brier": (sum((r["p"] - r["truth"]) ** 2 for r in valid) / len(valid)) if valid else None,
        "by_access": {}, "by_family_identified_exact": {}, "by_family_unidentified_commit": {},
        "verdicts_when_unidentified": dict(sorted(defaultdict(int, {
            v: sum(r["verdict"] == v for r in unidentified)
            for v in ("supported", "refuted", "insufficient")}).items())),
    }
    for access in sorted({r["access"] for r in valid}):
        cell = [r for r in valid if r["access"] == access]
        out["by_access"]["+".join(access) or "report_only"] = {
            "exact": rate(cell, lambda r: r["exact"]),
            "committed": rate(cell, committed)}
    for family in sorted({r["family"] for r in valid}):
        out["by_family_identified_exact"][family] = rate(
            [r for r in identified if r["family"] == family], lambda r: r["exact"])
        out["by_family_unidentified_commit"][family] = rate(
            [r for r in unidentified if r["family"] == family], committed)

    by_cell = {(r["incident"], r["access"]): r for r in valid}
    pairs = []
    for r in valid:
        if r["access"] != ():
            continue
        for extra in H1_CELLS.get(r["family"], []):
            other = by_cell.get((r["incident"], tuple(extra)))
            if other:
                pairs.append((committed(r), committed(other), r["pair_group"]))
    if pairs:
        only_extra = sum(1 for a, b, _ in pairs if b and not a)
        only_report = sum(1 for a, b, _ in pairs if a and not b)
        discordant = only_extra + only_report
        p_d_upper = clopper_pearson(discordant, len(pairs), 0.80)[1]
        n_pairs = ((Z_ALPHA * math.sqrt(p_d_upper) + Z_BETA * math.sqrt(
            max(0.0, p_d_upper - DELTA ** 2))) ** 2) / DELTA ** 2
        clusters = defaultdict(list)
        for r in unidentified:
            clusters[r["pair_group"]].append(int(committed(r)))
        rho, m = icc(list(clusters.values()))
        deff = 1 + (m - 1) * rho if rho is not None else None
        out["h1_stage1"] = {
            "pairs": len(pairs), "commit_report_only": sum(a for a, _, _ in pairs),
            "commit_with_irrelevant_channel": sum(b for _, b, _ in pairs),
            "only_irrelevant_commits": only_extra, "only_report_commits": only_report,
            "difference": (only_extra - only_report) / len(pairs),
            "discordance": discordant / len(pairs), "discordance_upper80": p_d_upper,
            "icc_commit_unidentified": rho, "mean_cluster_size": m, "design_effect": deff,
            "required_pairs_unadjusted": math.ceil(n_pairs),
            "required_pairs_with_design_effect": math.ceil(n_pairs * deff) if deff else None,
            "note": "Stage 1 is a pilot on development tasks; this is not an H1 test."}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    labels = json.loads((args.corpus / "labels.json").read_text())
    result = {"schema": "witness.evidence-access-stage1-analysis.v1", "model_calls": 0,
              "runs": {}}
    for run in args.runs:
        manifest = json.loads((run / "manifest.json").read_text())
        result["runs"][run.name] = {"model": manifest["model"], **analyze(run, labels)}
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        write_once(args.out / "analysis.json", text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
