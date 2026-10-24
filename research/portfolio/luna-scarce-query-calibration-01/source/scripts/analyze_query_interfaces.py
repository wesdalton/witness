"""Matched output-requirement contrasts; do not impute missing final artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.analyze_portfolio_pairs import paired_binary  # noqa: E402


def analyze(folder):
    manifest = json.loads((folder / "manifest.json").read_text())
    records = [json.loads(f.read_text()) for f in sorted(folder.glob("episode-*.json"))]
    by_key = {(r["spec"]["seed"], r["spec"]["truth"], r["spec"]["arm"],
               r["spec"]["output_mode"]): r for r in records}
    if len(by_key) != len(records):
        raise ValueError("Duplicate paired condition")
    planned = {(s["seed"], s["truth"], s["arm"], s["output_mode"])
               for s in manifest["episodes"]}
    if not set(by_key) <= planned:
        raise ValueError("Unplanned record")
    for seed, truth in sorted({key[:2] for key in planned}):
        same_case = [r for key, r in by_key.items() if key[:2] == (seed, truth)]
        reference = same_case[0] if same_case else None
        for record in same_case:
            if record["workspace_sha256"] != reference["workspace_sha256"]:
                raise ValueError("Substantive source differs within matched case")
            a = {k: v for k, v in record["initial_view"].items() if k != "peer_messages"}
            b = {k: v for k, v in reference["initial_view"].items() if k != "peer_messages"}
            if a != b:
                raise ValueError("Substantive initial evidence differs")
            expected = manifest["output_interfaces"][record["spec"]["output_mode"]]["system_prompt"]
            if record["system_prompt"] != expected:
                raise ValueError("Wrong intervention system prompt")
    if manifest.get("route_case_mode") == "same_program":
        for seed, arm, mode in sorted({(k[0], k[2], k[3]) for k in planned}):
            a, b = (by_key.get((seed, t, arm, mode)) for t in (False, True))
            if a and b and a["initial_view"] != b["initial_view"]:
                raise ValueError("Finite truth leaked through the initial model view")
    comparisons = []
    for truth in (False, True):
        for arm in ("neutral", "endorsement"):
            rows, missing = [], []
            seeds = sorted({s[0] for s in planned if s[1:3] == (truth, arm)})
            for seed in seeds:
                a = by_key.get((seed, truth, arm, "verdict"))
                b = by_key.get((seed, truth, arm, "program"))
                if not a or not b or a["status"] != "completed" or b["status"] != "completed":
                    missing.append(seed)
                    continue
                rows.append({
                    "seed": seed,
                    "verdict_correct": a["metrics"]["correct_verdict"],
                    "program_correct": b["metrics"]["correct_verdict"],
                    "brier_difference_program_minus_verdict":
                        b["metrics"]["brier"] - a["metrics"]["brier"],
                    "live_query_difference_program_minus_verdict":
                        sum(e["type"] == "tool" for e in b["events"])
                        - sum(e["type"] == "tool" for e in a["events"]),
                })
            comparisons.append({
                "truth": truth, "peer_arm": arm, "pairs": rows, "missing_seeds": missing,
                "mean_brier_difference_program_minus_verdict":
                    sum(r["brier_difference_program_minus_verdict"] for r in rows) / len(rows)
                    if rows else None,
                "accuracy_difference": paired_binary([
                    int(r["program_correct"]) - int(r["verdict_correct"]) for r in rows])
                    if rows else None,
            })
    peers = []
    cells = []
    for mode in ("verdict", "program"):
        for truth in (False, True):
            rows, missing = [], []
            seeds = sorted({s[0] for s in planned if s[1] == truth and s[3] == mode})
            for seed in seeds:
                a, b = (by_key.get((seed, truth, arm, mode))
                        for arm in ("neutral", "endorsement"))
                if not a or not b or a["status"] != "completed" or b["status"] != "completed":
                    missing.append(seed)
                    continue
                rows.append({
                    "seed": seed,
                    "neutral_correct": a["metrics"]["correct_verdict"],
                    "endorsement_correct": b["metrics"]["correct_verdict"],
                    "brier_difference_endorsement_minus_neutral":
                        b["metrics"]["brier"] - a["metrics"]["brier"],
                    "live_query_difference_endorsement_minus_neutral":
                        sum(e["type"] == "tool" for e in b["events"])
                        - sum(e["type"] == "tool" for e in a["events"]),
                })
            peers.append({
                "output_mode": mode, "truth": truth, "pairs": rows, "missing_seeds": missing,
                "accuracy_difference": paired_binary([
                    int(r["endorsement_correct"]) - int(r["neutral_correct"]) for r in rows])
                    if rows else None,
            })
            for arm in ("neutral", "endorsement"):
                selected = [r for r in records if r["spec"]["output_mode"] == mode
                            and r["spec"]["truth"] == truth and r["spec"]["arm"] == arm]
                complete = [r for r in selected if r["status"] == "completed"]
                tools = [e for r in selected for e in r["events"] if e["type"] == "tool"]
                cells.append({
                    "output_mode": mode, "truth": truth, "peer_arm": arm,
                    "attempted": len(selected), "completed": len(complete),
                    "correct": sum(r["metrics"]["correct_verdict"] for r in complete),
                    "mean_brier": sum(r["metrics"]["brier"] for r in complete) / len(complete)
                                  if complete else None,
                    "live_queries": len(tools),
                    "query_errors": sum(e["result"]["exit_code"] != 0 for e in tools),
                    "episodes_with_query": sum(any(e["type"] == "tool" for e in r["events"])
                                               for r in selected),
                    "reported_cost_usd": str(sum(
                        (Decimal(str(e["usage"]["cost"])) for r in selected for e in r["events"]
                         if e["type"] == "model"), Decimal(0))),
                })
    return {
        "schema": "witness.output-requirement-analysis.v1",
        "manifest_sha256": hashlib.sha256((folder / "manifest.json").read_bytes()).hexdigest(),
        "planned": len(planned), "attempted": len(records),
        "status_counts": {status: sum(r["status"] == status for r in records)
                          for status in sorted({r["status"] for r in records})},
        "output_requirement_contrasts": comparisons,
        "secondary_peer_contrasts": peers, "cells": cells,
        "interpretation": "Exploratory matched contrasts. Four seed blocks, not independent "
        "truth-state/peer repetitions. Source-only evidence is legitimate. Unrequested final "
        "programs are unmeasured, not failures. No mediation claim or equivalence from a wide CI.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.folder)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
