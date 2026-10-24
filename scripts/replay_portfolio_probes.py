"""Replay inline Python probes against v2 variants; local execution, no inference."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab.agent_study import save  # noqa: E402
from swarm_lab.portfolio_v2_cases import ContractWorkspace  # noqa: E402


def extract(command):
    """Only literal Python stdin heredocs; unparsed commands remain unmeasured."""
    lines = command.splitlines()
    blocks, index = [], 0
    pattern = r"""^\s*python(?:3)?\s+-\s+<<\s*(['"]?)([A-Za-z_][A-Za-z_0-9]*)\1\s*$"""
    while index < len(lines):
        matched = re.match(pattern, lines[index])
        if not matched:
            index += 1
            continue
        end = index + 1
        while end < len(lines) and lines[end] != matched.group(2):
            end += 1
        if end == len(lines):
            break
        code = "\n".join(lines[index+1:end]) + "\n"
        ast.parse(code)
        blocks.append(code)
        index = end + 1
    return blocks


def replay(episode_path):
    episode = json.loads(episode_path.read_text())
    manifest = json.loads((episode_path.parent / "manifest.json").read_text())
    cases = {c["id"]: c for c in episode["portfolio"]["cases"]}
    probes, unmeasured, seen = [], [], {}
    for event in episode["events"]:
        if event["type"] != "tool":
            continue
        cid = event["claim_id"]
        family = cases[cid]["family"]
        try:
            codes = extract(event["arguments"]["command"])
        except SyntaxError:
            codes = []
        if not codes:
            unmeasured.append(event["evidence_id"])
            continue
        for code in codes:
            key = (family, hashlib.sha256(code.encode()).hexdigest())
            if key in seen:
                seen[key]["origin_evidence_ids"].append(event["evidence_id"])
                continue
            item = {"family": family, "code": code, "sha256": key[1],
                    "origin_evidence_ids": [event["evidence_id"]], "variants": []}
            seen[key] = item
            settings = [(True, "historical", "repaired"), (False, "historical", "historical")]
            if family != "routing":
                settings.append((False, "residual", "residual"))
            for truth, variant, label in settings:
                workspace = ContractWorkspace(family, truth, manifest["image"], variant)
                try:
                    result = workspace.execute(["python", "-"], code)
                    item["variants"].append({"variant": label, "result": result,
                                             "source_sha256": workspace.hashes()})
                finally:
                    workspace.close()
            good = item["variants"][0]["result"]
            for variant in item["variants"][1:]:
                bad = variant["result"]
                usable = not any(r["timed_out"] or r["output_truncated"] for r in (good, bad))
                variant["differential_observation"] = usable and (
                    good["exit_code"], good["stdout"], good["stderr"]) != (
                    bad["exit_code"], bad["stdout"], bad["stderr"])
                variant["assertion_candidate"] = usable and (
                    good["exit_code"] == 0 and bad["exit_code"] != 0
                    and "AssertionError" in bad["stderr"])
            probes.append(item)
    return {
        "schema": "witness.probe-replay.v1", "episode": str(episode_path.relative_to(ROOT)),
        "episode_sha256": hashlib.sha256(episode_path.read_bytes()).hexdigest(),
        "replay_environment": "portfolio-v2", "image": manifest["image"],
        "implementation_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (
                Path(__file__), ROOT / "swarm_lab/portfolio_v2_cases.py",
                ROOT / "swarm_lab/agent_workspace.py")},
        "probes": probes, "unmeasured_command_evidence_ids": unmeasured,
        "interpretation": (
            "Differential observations require semantic review. Different text or an "
            "exception alone is not proof of detecting a bug. Unparsed commands and "
            "source reasoning are unmeasured, not failed verification."),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.episode.resolve())
    save(args.out, result)
    print(json.dumps({"unique_inline_probes": len(result["probes"]),
                      "unmeasured_commands": len(result["unmeasured_command_evidence_ids"])}))


if __name__ == "__main__":
    main()
