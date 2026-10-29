"""Summarize complete Witness episodes without treating dependent agents as replicates."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def summarize(record: dict, source_sha256: str = "") -> dict:
    if record.get("schema") != "witness.llm.v1":
        raise ValueError("Expected a decision-harness run, not a mechanistic simulation")
    events = record["events"]
    manifests = [e for e in events if e.get("type") == "manifest"]
    completions = [e for e in events if e.get("type") == "completion"]
    rounds = [e for e in events if e.get("type") == "round"]
    decisions = [e for e in events if e.get("type") == "decision"]
    if len(manifests) != 1 or len(completions) != 1:
        raise ValueError("Run must contain one manifest and one completion record")
    manifest = manifests[0]
    if completions[0]["status"] not in {"success", "completed_with_errors"}:
        raise ValueError("Interrupted/failed episode is not a completed experiment")
    c = record["config"]
    if len(rounds) != c["rounds"] or [r["round"] for r in rounds] != list(
        range(1, c["rounds"] + 1)
    ):
        raise ValueError("Missing or duplicate round observations")
    if len(decisions) != c["population"] * c["rounds"]:
        raise ValueError("Missing decision observations")
    for row in rounds:
        if row["effort"] != row["check_requests"] * 4 + row["messages"]:
            raise ValueError("Action accounting mismatch")
    last = rounds[-1]
    completion = completions[0]
    return {
        "source_sha256": source_sha256,
        "kind": record["kind"],
        "status": completion["status"],
        "model": manifest["requested_model"],
        "harness_sha256": manifest["harness_sha256"],
        "prompt_sha256": manifest["prompt_sha256"],
        "artifact_sha256": manifest["artifact_sha256"],
        "fixture": record["fixture"],
        "truth": record["truth"],
        "config": c,
        "decision_slots": len(decisions),
        "invalid_or_failed_decisions": sum(e.get("error") is not None for e in decisions),
        "invalid_model_decisions": sum(e.get("error") == "invalid_decision" for e in decisions),
        # Fields below are absent from v0.1 records; None means "not measured".
        "parse_mode": manifest.get("parse_mode"),
        "rng_scheme": manifest.get("rng_scheme"),
        "accepted_format_violations": sum(bool(e.get("format_violation")) for e in decisions)
        if "parse_mode" in manifest
        else None,
        "invalid_lenient_recoverable": sum(bool(e.get("lenient_recoverable")) for e in decisions)
        if "parse_mode" in manifest
        else None,
        "stop_reasons": dict(Counter(str(e.get("stop_reason")) for e in decisions))
        if "parse_mode" in manifest
        else None,
        "infrastructure_failed_slots": sum(
            str(e.get("error", "")).startswith("provider_error:") for e in decisions
        ),
        "eligible_for_behavioral_comparison": not any(
            str(e.get("error", "")).startswith("provider_error:") for e in decisions
        ),
        "agents_executing_check": len(
            {e["agent"] for e in decisions if e["executed_action"] == "check"}
        ),
        "forced_check_actions": sum(
            e["executed_action"] == "check" and e["forced_check"] for e in decisions
        ),
        "voluntary_check_actions": sum(
            e["executed_action"] == "check" and not e["forced_check"] for e in decisions
        ),
        "check_requests": last["check_requests"],
        "probe_deliveries": last["probe_deliveries"],
        "pending_checks": last["pending_checks"],
        "messages": last["messages"],
        "effort": last["effort"],
        "unused_effort": c["population"] * c["budget"] - last["effort"],
        "final_wrong": last["wrong"],
        "final_uncertain": last["uncertain"],
        "final_correct": 1 - last["wrong"] - last["uncertain"],
        "final_brier": last["brier"],
        "peak_wrong": max(r["wrong"] for r in rounds),
        "mean_wrong": sum(r["wrong"] for r in rounds) / len(rounds),
        "mean_brier": sum(r["brier"] for r in rounds) / len(rounds),
        "usage": completion.get("usage_totals", {}),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", type=Path, nargs="+")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Output exists; choose a new path")
    rows = []
    seen = set()
    for path in args.runs:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest in seen:
            parser.error("Duplicate run supplied; it is not an independent replicate")
        seen.add(digest)
        rows.append(summarize(json.loads(raw), digest))
    result = {
        "schema": "witness.episode_summary.v1",
        "episodes": rows,
        "interpretation": [
            "Each row is one dependent multi-agent episode, not N independent samples.",
            "Mean error covers completed rounds 1..T; the harness has no round-zero metric.",
            "Scripted and real-model kinds remain separate; no inferential statistics computed.",
            "Repeated ledger fixtures constitute one case family, not task diversity.",
            "Usage totals are provider-reported tokens, not inferred dollar charges.",
            "Infrastructure-failed episodes are retained but excluded from behavior comparisons.",
            "Invalid model outputs are outcomes; infrastructure failures are not model decisions.",
            "Slots include blocked attempts; paid dispatch counts require the budget ledger.",
            "Executed checks include forced actions; voluntary_check_actions excludes these.",
            "Checks retrieve one recorded probe root; they are not independent evidence.",
        ],
    }
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Summarized {len(rows)} complete episodes without pooling their agents as replicates.")


if __name__ == "__main__":
    main()
