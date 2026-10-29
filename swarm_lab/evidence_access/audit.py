"""Stage 1 calibration runner: one fresh-context auditor response per (incident, access set).

Dry run by default: prints the plan and its worst-case reservation. `--live` checks
the gates, the phase budget and the provider key, then dispatches with no retries.
Each episode is written once. The auditor never sees labels, families or pairing.
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from swarm_lab.core.budget import PHASE_LEDGER, ROOT, BudgetError, PhaseBudget, money
from swarm_lab.core.client import ResponsesClient, catalog, load_key, preflight_key
from swarm_lab.core.records import digest, save, tool_schema
from swarm_lab.evidence_access.corpus import ACCESS_SETS, expected_verdict, observe

SYSTEM = """You audit claims about runs of an automated software evaluation.
You receive one claim and the evidence you have been granted. Decide whether that
evidence supports the claim, refutes it, or is insufficient to decide it.
Answer "insufficient" when the evidence you were given cannot settle the claim.
Call submit once with your verdict, the probability that the claim is true, the
evidence channels your verdict relies on, and a reason of at most three sentences."""
VERDICTS = ("supported", "refuted", "insufficient")
CHANNEL_NAMES = ("report", "artifacts", "manifest", "replay")
SUBMIT = tool_schema("submit", "Submit the audit verdict.", {
    "verdict": {"type": "string", "enum": list(VERDICTS)},
    "p_claim_true": {"type": "number"},
    "evidence_used": {"type": "array", "items": {"type": "string", "enum": list(CHANNEL_NAMES)}},
    "reason": {"type": "string"},
}, ["verdict", "p_claim_true", "evidence_used", "reason"])
STAGE1 = {"openai/gpt-6-luna": [s for s in ACCESS_SETS],
          "openai/gpt-6.1-sol": [frozenset(), frozenset({"artifacts", "manifest", "replay"})]}
CEILINGS = {"openai/gpt-6-luna": Decimal("3"), "openai/gpt-6.1-sol": Decimal("6")}


def access_name(access) -> str:
    return "+".join(sorted(access)) or "report_only"


def user_message(incident: dict, access) -> str:
    granted = observe(incident, access)
    claim = granted["report"]["claim"]
    return (f"Claim: {claim}\n\nGranted evidence channels: "
            f"{', '.join(granted)}\n\nEvidence (JSON):\n"
            + json.dumps(granted, indent=1, sort_keys=True))


def load_corpus(path: Path) -> tuple[list[dict], dict, dict]:
    incidents = [json.loads(line) for line in (path / "incidents.jsonl").read_text().splitlines()]
    labels = json.loads((path / "labels.json").read_text())
    gates = json.loads((path / "gates.json").read_text())
    if not gates["passed"]:
        raise BudgetError("Corpus gates did not pass; no model calls")
    for incident in incidents:
        incident.update(labels[incident["id"]])
    separating = {g: set(c) for g, c in gates["separating_channels"].items()}
    return incidents, labels, separating


def plan(incidents: list[dict], model: str, split: str = "dev") -> list[dict]:
    chosen = [i for i in incidents if i["split"] == split]
    return [{"episode": f"{n:04d}", "incident": i["id"], "access": sorted(a)}
            for n, (i, a) in enumerate((i, a) for i in chosen for a in STAGE1[model])]


def validate(arguments: dict) -> dict:
    if set(arguments) != {"verdict", "p_claim_true", "evidence_used", "reason"}:
        raise ValueError("unexpected fields")
    p = arguments["p_claim_true"]
    if arguments["verdict"] not in VERDICTS or not isinstance(p, (int, float)) or not 0 <= p <= 1:
        raise ValueError("invalid verdict or probability")
    if any(c not in CHANNEL_NAMES for c in arguments["evidence_used"]):
        raise ValueError("unknown evidence channel")
    return arguments


def run_episode(spec: dict, incident: dict, separating: dict, client) -> dict:
    access = frozenset(spec["access"])
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_message(incident, access)}]
    record = {"schema": "witness.evidence-access-episode.v1", **spec,
              "started_at": datetime.now(UTC).isoformat(),
              "prompt_sha256": digest(json.dumps(messages, sort_keys=True).encode()),
              "expected": expected_verdict(incident, access, separating)}
    message, event = client.generate(messages, final=True)
    record["model_event"] = {k: v for k, v in event.items() if k != "message"}
    calls = message.get("tool_calls") or []
    try:
        if len(calls) != 1 or calls[0]["function"]["name"] != "submit":
            raise ValueError("expected exactly one submit call")
        submission = validate(json.loads(calls[0]["function"]["arguments"]))
        record.update(status="completed", submission=submission,
                      exact=submission["verdict"] == record["expected"])
    except (ValueError, KeyError, json.JSONDecodeError) as error:
        record.update(status="invalid_output", error=str(error), raw=message, exact=None)
    record["finished_at"] = datetime.now(UTC).isoformat()
    return record


def snapshot(out: Path) -> dict[str, str]:
    """Copy the exact runner source into the run and return its hashes."""
    paths = [*sorted((ROOT / "swarm_lab/evidence_access").glob("*.py")),
             *(ROOT / "swarm_lab/core" / n for n in ("budget.py", "client.py", "records.py"))]
    hashes = {}
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        target = out / "source" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(path.read_bytes())
        hashes[rel] = digest(path.read_bytes())
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--model", choices=list(STAGE1), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    incidents, _, separating = load_corpus(args.corpus)
    by_id = {i["id"]: i for i in incidents}
    episodes = plan(incidents, args.model)
    ceiling = CEILINGS[args.model]
    summary = {"model": args.model, "episodes": len(episodes), "batch_ceiling_usd": str(ceiling),
               "access_sets": sorted({access_name(e["access"]) for e in episodes}),
               "phase": PhaseBudget(PHASE_LEDGER).summary()}
    if not args.live:
        print(json.dumps(summary, indent=2))
        return 0
    args.out.mkdir(parents=True, exist_ok=False)
    _, input_price, output_price = catalog(args.model)
    key = load_key(ROOT / ".env")
    if not key:
        raise BudgetError("No provider credential")
    key_limits = preflight_key(key, money(ceiling))
    batch = uuid.uuid4().hex
    corpus_files = {name: digest((args.corpus / name).read_bytes())
                    for name in ("incidents.jsonl", "labels.json", "gates.json")}
    save(args.out / "manifest.json", {
        "source_sha256": snapshot(args.out), "corpus_sha256": corpus_files,
        "schema": "witness.evidence-access-run.v1", "batch": batch, "model": args.model,
        "reasoning": "medium", "max_output_tokens": 4096, "system_prompt": SYSTEM,
        "submit_tool": SUBMIT, "corpus": str(args.corpus.relative_to(ROOT)),
        "episodes": episodes, "batch_ceiling_usd": str(ceiling), "key_limits": key_limits,
        "started_at": datetime.now(UTC).isoformat()})
    client = ResponsesClient(key, args.model, PhaseBudget(PHASE_LEDGER), batch, money(ceiling),
                             input_price, output_price, max_tokens=4096, tools=[SUBMIT],
                             reasoning="medium")
    completed = 0
    for spec in episodes:
        record = run_episode(spec, by_id[spec["incident"]], separating, client)
        save(args.out / f"episode-{spec['episode']}.json", record)
        completed += 1
    save(args.out / "completion.json", {"completed": completed,
                                        "finished_at": datetime.now(UTC).isoformat()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
