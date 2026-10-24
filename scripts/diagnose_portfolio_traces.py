"""Descriptive evidence and probability-consistency checks; no outcome repair."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def diagnose(folder):
    episodes, groups = [], defaultdict(list)
    for path in sorted(folder.glob("episode-*.json")):
        data = json.loads(path.read_text())
        case_by_id = {case["id"]: case for case in data["portfolio"]["cases"]}
        tools = [event for event in data["events"] if event["type"] == "tool"]
        counts = Counter(event["claim_id"] for event in tools)
        nonzero = sum(event["result"]["exit_code"] != 0 for event in tools)
        assessments = (data["submission"] or {}).get("assessments", [])
        rows = []
        for assessment in assessments:
            cid, p = assessment["claim_id"], assessment["p_support"]
            verdict = assessment["verdict"]
            contradiction = ((verdict == "refuted" and p > 0.5)
                             or (verdict == "supported" and p < 0.5))
            rows.append({
                **case_by_id[cid], **assessment,
                "inspected": cid in counts,
                "commands": counts[cid],
                "verdict_probability_contradiction": contradiction,
                "squared_error_literal_probability": (p-case_by_id[cid]["truth"])**2,
            })
        row = {"file": path.name, "spec": data["spec"], "status": data["status"],
               "model_responses": sum(e["type"] == "model" for e in data["events"]),
               "commands": len(tools), "nonzero_exit_commands": nonzero,
               "claims": rows,
               "target": data["portfolio"]["target"],
               "target_selected_from_events": data["portfolio"]["target"] in counts}
        if data["metrics"] is not None:
            assert row["target_selected_from_events"] == data["metrics"]["target_investigated"]
        episodes.append(row)
        groups[data["spec"]["arm"]].append(row)
    summaries = {}
    for arm, group in groups.items():
        completed = [e for e in group if e["status"] == "completed"]
        claims = [c for e in completed for c in e["claims"]]
        summaries[arm] = {
            "attempted_episodes": len(group), "completed_episodes": len(completed),
            "commands": sum(e["commands"] for e in group),
            "model_responses": sum(e["model_responses"] for e in group),
            "nonzero_exit_commands": sum(e["nonzero_exit_commands"] for e in group),
            "probability_contradictions": sum(c["verdict_probability_contradiction"]
                                             for c in claims),
            "inspected_claims": sum(c["inspected"] for c in claims),
            "uninspected_software_assessments": [
                {"seed": e["spec"]["seed"], "claim_id": c["id"], "family": c["family"],
                 "truth": c["truth"], "verdict": c["verdict"], "p_support": c["p_support"],
                 "target": c["id"] == e["target"]}
                for e in completed for c in e["claims"]
                if not c["inspected"] and c["family"] != "control"],
        }
    return {"schema": "witness.portfolio-diagnostics.v1", "batch": folder.name,
            "summaries": summaries, "episodes": episodes,
            "interpretation": "Descriptive diagnostics added after observing a probability/"
            "verdict inconsistency in the exploratory screen. Preserve literal probabilities; "
            "do not invert or impute. Nonzero exit codes can be informative counterexamples, "
            "and tool counts are not verification quality. No new confirmatory tests."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.folder)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"episodes": len(result["episodes"]),
                      "probability_contradictions": {
                          k: v["probability_contradictions"]
                          for k, v in result["summaries"].items()}}))


if __name__ == "__main__":
    main()
