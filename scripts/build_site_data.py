"""Build the compact, public pilot-decision asset used by the website."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "website/dist/assets/pilot-decisions.json"
EPISODES = (
    ("false", "False report", "luna-paced-false-seed42/pytest_module_shadow-reports.json"),
    ("true", "True report", "luna-paced-pair-seed42/honest_fix-reports.json"),
)


def episode(key: str, label: str, relative: str) -> dict:
    path = ROOT / "research/swarm" / relative
    raw = path.read_bytes()
    record = json.loads(raw)
    events = record["events"]
    manifest = next(e for e in events if e["type"] == "manifest")
    decisions = []
    for e in (e for e in events if e["type"] == "decision"):
        evidence = e["view"]["evidence"]
        chosen = e["decision"]["action"] if e["decision"] else None
        decisions.append(
            {
                "round": e["round"],
                "agent": e["agent"],
                "chosen": chosen,
                "executed": e["executed_action"],
                "p": e["decision"]["p_support"] if e["decision"] else None,
                "message": e["decision"]["message"] if e["decision"] else None,
                "sources": e["decision"]["sources"] if e["decision"] else [],
                "error": e["error"],
                "raw_output": e["raw_output"] if e["error"] else None,
                "previous_p": e["view"]["previous_support"],
                "budget_before": e["view"]["budget"],
                "pending": e["view"]["pending"],
                "has_report": any(x["kind"] == "report" for x in evidence),
                "has_probe": any(x["kind"] == "probe" for x in evidence),
                "peer_messages": sum(x["kind"] == "peer" for x in evidence),
                "recipient": e.get("recipient"),
            }
        )
    rounds = [
        {k: e[k] for k in ("round", "wrong", "uncertain", "check_requests", "probe_deliveries",
                           "messages", "effort")}
        for e in events
        if e["type"] == "round"
    ]
    return {
        "key": key,
        "label": label,
        "truth": record["truth"],
        "fixture": record["fixture"],
        "model": manifest["requested_model"],
        "config": record["config"],
        "graph": manifest["graph"],
        "source_path": f"research/swarm/{relative}",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "decisions": decisions,
        "rounds": rounds,
    }


def build() -> dict:
    data = {
        "schema": "witness.site.pilot_decisions.v1",
        "note": "Derived from recorded pilot episodes; raw records are in the source archive.",
        "episodes": [episode(*row) for row in EPISODES],
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    return data


if __name__ == "__main__":
    result = build()
    print(json.dumps({"path": str(OUT), "episodes": len(result["episodes"])}))
