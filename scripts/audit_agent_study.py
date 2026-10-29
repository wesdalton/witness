"""Reconcile saved live-auditor traces, source snapshots and the phase ledger; no API calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab.core.archive import Archive  # noqa: E402
from swarm_lab.core.budget import PHASE_LIMIT, exposure  # noqa: E402


def read(path):
    return json.loads(path.read_text())


def audit(root: Path):
    ledger = [json.loads(line) for line in (root / "budget.jsonl").read_text().splitlines()]
    reservations = {row["request"]: row for row in ledger if row["type"] == "reserve"}
    completions = {row["request"]: row for row in ledger if row["type"] == "complete"}
    errors, warnings, batches, seen = [], [], [], set()
    repository = Archive(root.resolve().parents[1])
    packed = repository.packed()
    if len(reservations) != sum(row["type"] == "reserve" for row in ledger):
        errors.append("Duplicate request reservation")
    if len(completions) != sum(row["type"] == "complete" for row in ledger):
        errors.append("Duplicate request completion")
    manifests = list(root.glob("*/manifest.json"))
    manifests.extend((root.parent / "portfolio").glob("*/manifest.json"))
    manifests.extend((root.parent / "experiments").glob("*/runs/*/manifest.json"))
    for folder in sorted(p.parent for p in manifests):
        manifest = read(folder / "manifest.json")
        portfolio = manifest.get("schema", "").startswith("witness.portfolio-manifest.")
        query_audit = manifest.get("schema") == "witness.query-manifest.v1"
        adjudication_path = folder / "adjudication.json"
        adjudication = read(adjudication_path) if adjudication_path.exists() else None
        score_valid = not adjudication or adjudication.get("reference_labels_valid", True)
        if not score_valid:
            warnings.append(f"{folder.name}: invalid reference labels; accuracy/Brier excluded")
        if adjudication and not adjudication.get("universal_correctness_claim_valid", True):
            warnings.append(
                f"{folder.name}: finite scores retained; universal program correctness unsupported")
        source_dir = (folder / "source").resolve().relative_to(repository.root)
        snapshot = (folder / "source").exists() or any(
            name.startswith(source_dir.as_posix() + "/") for name in packed)
        if not snapshot:
            warnings.append(f"{folder.name}: no full source snapshot; hashes/configuration only")
        else:
            for rel, expected in manifest["source_sha256"].items():
                try:
                    raw = repository.read_bytes(source_dir / rel)
                except FileNotFoundError:
                    raw = None
                if raw is None or hashlib.sha256(raw).hexdigest() != expected:
                    errors.append(f"{folder.name}: source mismatch: {rel}")
        grouped = defaultdict(list)
        records = []
        for path in sorted(folder.glob("episode-*.json")):
            episode = read(path)
            records.append(episode)
            trace = [json.loads(line)
                     for line in path.with_suffix(".jsonl").read_text().splitlines()]
            if trace[1:-1] != episode["events"]:
                errors.append(f"{folder.name}/{path.name}: event trace mismatch")
            if trace[-1]["status"] != episode["status"]:
                errors.append(f"{folder.name}/{path.name}: completion mismatch")
            if trace[-1]["submission"] != episode["submission"]:
                errors.append(f"{folder.name}/{path.name}: submission mismatch")
            if portfolio:
                tools = [e for e in episode["events"] if e["type"] == "tool"]
                inspected = {e["claim_id"] for e in tools}
                if len(inspected) > episode["spec"]["budget"] or len(tools) > 24:
                    errors.append(f"{folder.name}/{path.name}: investigation budget mismatch")
                if episode["submission"]:
                    truth = {c["id"]: c["truth"] for c in episode["portfolio"]["cases"]}
                    assessments = episode["submission"]["assessments"]
                    brier = sum((a["p_support"]-truth[a["claim_id"]])**2
                                for a in assessments) / len(truth)
                    if brier != episode["metrics"]["brier"]:
                        errors.append(f"{folder.name}/{path.name}: score mismatch")
                    if sorted(inspected) != episode["metrics"]["investigated"]:
                        errors.append(f"{folder.name}/{path.name}: allocation mismatch")
            if query_audit:
                query_events = [e for e in episode["events"] if e["type"] == "tool"]
                query_budget = episode["spec"].get("query_budget", 8)
                if len(query_events) > query_budget or any(
                        e["queries_remaining"] != query_budget-i
                        for i, e in enumerate(query_events, 1)):
                    errors.append(f"{folder.name}/{path.name}: query budget mismatch")
            if query_audit and episode["submission"]:
                expected_brier = (episode["submission"]["p_support"]-episode["spec"]["truth"])**2
                if expected_brier != episode["metrics"]["brier"]:
                    errors.append(f"{folder.name}/{path.name}: query score mismatch")
            for event in episode["events"]:
                if event["type"] != "model":
                    continue
                request = event["request_id"]
                if request in seen:
                    errors.append(f"Duplicate response event: {request}")
                seen.add(request)
                reserved, complete = reservations.get(request), completions.get(request)
                if not reserved or not complete:
                    errors.append(f"Response missing budget records: {request}")
                    continue
                if reserved["batch"] != manifest["batch"]:
                    errors.append(f"Wrong budget batch: {request}")
                if complete["response_id"] != event["response_id"]:
                    errors.append(f"Provider response ID mismatch: {request}")
                if complete["usage"] != event["usage"]:
                    errors.append(f"Usage mismatch: {request}")
            grouped[(episode["spec"]["arm"], episode["spec"].get("output_mode", "legacy"))].append(
                episode)
        rows = []
        for (arm, output_mode), episodes in sorted(grouped.items()):
            tool_lists = [[e for e in ep["events"] if e["type"] == "tool"] for ep in episodes]
            submitted = [ep for ep in episodes if ep["submission"]]
            cost = sum((Decimal(str(e["usage"]["cost"])) for ep in episodes
                        for e in ep["events"] if e["type"] == "model"), Decimal(0))
            if portfolio:
                rows.append({
                    "arm": arm, "attempted": len(episodes), "submitted": len(submitted),
                    "correct_claim_verdicts": sum(ep["metrics"]["correct_verdicts"]
                                                  for ep in submitted) if score_valid else None,
                    "uncertain_claim_verdicts": sum(ep["metrics"]["uncertain_verdicts"]
                                                    for ep in submitted),
                    "mean_brier": sum(ep["metrics"]["brier"] for ep in submitted)
                    / len(submitted) if submitted and score_valid else None,
                    "reference_labels_valid": score_valid,
                    "target_investigated": sum(ep["metrics"]["target_investigated"]
                                               for ep in submitted),
                    "commands": sum(map(len, tool_lists)),
                    "nonzero_exit_commands": sum(e["result"]["exit_code"] != 0
                                                for ts in tool_lists for e in ts),
                    "reported_cost_usd": str(cost),
                })
                continue
            if query_audit:
                with_artifact = [ep for ep in submitted if "audit_sql" in ep["submission"]]
                rows.append({
                    "arm": arm, "output_mode": output_mode,
                    "attempted": len(episodes), "submitted": len(submitted),
                    "correct_claim_verdicts": sum(ep["metrics"]["correct_verdict"]
                                                  for ep in submitted),
                    "correct_sql_on_observed_database": sum(
                        ep["metrics"]["audit_sql_correct_this_database"] for ep in with_artifact),
                    "submitted_sql_artifacts": len(with_artifact),
                    "mean_brier": sum(ep["metrics"]["brier"] for ep in submitted)
                    / len(submitted) if submitted else None,
                    "live_queries": sum(map(len, tool_lists)),
                    "reported_cost_usd": str(cost),
                })
                continue
            rows.append({
                "arm": arm, "attempted": len(episodes), "submitted": len(submitted),
                "correct": sum(ep["submission"]["verdict"] == (
                    "supported" if ep["spec"]["truth"] else "refuted") for ep in submitted),
                "any_acquisition": sum(bool(ts) for ts in tool_lists),
                "source_read": sum(any(t["name"] == "read_file" for t in ts) for ts in tool_lists),
                "python_execution": sum(any(t["name"] == "run_python" for t in ts)
                                        for ts in tool_lists),
                "supplied_tests": sum(any(t["name"] == "run_tests" for t in ts)
                                      for ts in tool_lists),
                "reported_cost_usd": str(cost),
            })
        batches.append({"batch": folder.name, "status_counts": dict(Counter(
            ep["status"] for ep in records)), "arms": rows})
    missing = set(reservations) - seen
    if missing:
        warnings.append(f"{len(missing)} dispatched requests lack response events; review ledger")
    reserved = sum((Decimal(r["usd"]) for r in reservations.values()), Decimal(0))
    reported = sum((Decimal(r["reported_cost_usd"]) for r in completions.values()
                    if r["reported_cost_usd"] is not None), Decimal(0))
    committed = exposure(ledger)
    if committed > PHASE_LIMIT or reported > reserved:
        errors.append("Phase spend/reservation invariant failed")
    return {"schema": "witness.live-auditor-audit.v2", "errors": errors, "warnings": warnings,
            "requests": len(reservations), "exposure_usd": str(committed),
            "reserved_usd": str(reserved), "reported_cost_usd": str(reported),
            "batches": batches}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "research/agent-study")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        with args.out.open("x") as stream:
            stream.write(text)
    print(text)
    return bool(result["errors"])


if __name__ == "__main__":
    raise SystemExit(main())
