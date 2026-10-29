"""Negative-control replays of archived probes; no model calls or downloads."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from swarm_lab.core.archive import Archive, digest, write_once  # noqa: E402
from swarm_lab.legacy.portfolio_v2_cases import ContractWorkspace  # noqa: E402

EXPERIMENT = "20261028-probe-repeatability-v1"
PROTOCOL = """# Archived-probe repeatability negative controls

Exploratory measurement audit, frozen before new local replays. Initial inspection
found object addresses in three of 76 existing archived probes. Include ALL 76,
not only the suspicious examples. No new LLM inference, downloads or API spending.
This is independent work on existing evidence; the blocked repository-corpus
setup remains stopped.

Question: can the raw tuple (exit code, stdout, stderr) differ when exactly the
same agent-written probe runs on exactly the same implementation? If so, an
unqualified between-implementation text difference cannot count as fault detection.
The historical replay tool already calls these observations candidates requiring
semantic review. This audit tests that warning; it does not change original scores.

Population: every probe in research/portfolio/*/probe-replay*.json at freeze time.
Deduplicate by (family, code SHA-256), retaining ALL origins. Snapshot the selection,
source and input hashes. For each probe and each archived implementation variant,
execute twice in fresh isolated containers with the original pinned image. Require
current workspace source hashes to match the archived hashes before executing.
Stop on mismatched provenance. Keep raw outputs and failed/timed-out executions.

Primary endpoint: unequal raw signatures across the two identical-source repeats.
Secondary: archived raw between-variant differences erased solely by replacing
Python object/function repr addresses with a placeholder. This deliberately narrow
normalization must not erase ordinary hexadecimal payloads or numeric results.
Report timeouts and truncated output separately; do not count them as comparisons.
No repeatability claim extends beyond two repetitions. Finite source-consistency
controls do not establish a correct oracle; source dumps and API misuse still need
manual review. Report all suspect probes with code and provenance.

Decision: if negative controls trigger, future paid peer tests require a semantic
outcome extractor or assertion oracle plus repeated same-source controls. Otherwise
retain the current conservative semantic-review rule. This is a measurement finding
within Witness, not proof of a social effect or research novelty. Test replay and
oracle-quality measurement overlap https://arxiv.org/html/2607.28871 and
https://arxiv.org/html/2610.32548.
"""


def signature(result):
    return result["exit_code"], result["stdout"], result["stderr"]


def usable(result):
    return not (result["timed_out"] or result["output_truncated"])


def normalize_repr(text):
    return re.sub(r"(<[^<>\n]*\b(?:object|function)\b[^<>\n]* at )0x[0-9a-fA-F]+(>)",
                  r"\1<address>\2", text)


def normalized_signature(result):
    return result["exit_code"], normalize_repr(result["stdout"]), normalize_repr(result["stderr"])


def collect():
    selected = {}
    for path in sorted((ROOT / "research/portfolio").glob("*/probe-replay*.json")):
        record = json.loads(path.read_text())
        manifest_path = ROOT / record["episode"]
        manifest = json.loads((manifest_path.parent / "manifest.json").read_text())
        for probe in record["probes"]:
            sha = hashlib.sha256(probe["code"].encode()).hexdigest()
            if sha != probe["sha256"]:
                raise ValueError("Archived probe hash mismatch")
            key = (probe["family"], sha)
            origin = {"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                      "episode": record["episode"],
                      "evidence_ids": probe["origin_evidence_ids"]}
            if key in selected:
                selected[key]["origins"].append(origin)
            else:
                selected[key] = {**probe, "origins": [origin], "image": manifest["image"]}
    return list(selected.values())


def main():
    archive = Archive(ROOT)
    if archive.audit()["errors"]:
        raise ValueError("Archive integrity check failed")
    probes = collect()
    if len(probes) != 76:
        raise ValueError("Input population changed; review a new protocol")
    archive.create_experiment(EXPERIMENT, "Probe replay repeatability controls",
                              "Do identical-source replays produce spurious differences?", PROTOCOL)
    gate = archive.new_bundle(EXPERIMENT, "gates", "input-selection")
    write_once(gate / "selection.json", probes)
    archive.seal(EXPERIMENT + ".inputs", gate, kind="inputs", title="76 archived probes",
                 experiment=EXPERIMENT, parents=[EXPERIMENT + ".design"])
    run = archive.new_bundle(EXPERIMENT, "runs", "repeat-01")
    sources = [Path(__file__), ROOT / "swarm_lab/legacy/portfolio_v2_cases.py",
               ROOT / "swarm_lab/legacy/portfolio_cases.py",
               ROOT / "swarm_lab/legacy/agent_workspace.py",
               ROOT / "swarm_lab/core/archive.py"]
    for path in sources:
        write_once(run / "source" / path.relative_to(ROOT), path.read_text())
    write_once(run / "manifest.json", {
        "schema": "witness.local-replay-manifest.v1", "batch": EXPERIMENT,
        "model_inference": False, "probes": len(probes),
        "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in sources},
        "input_bundle": EXPERIMENT + ".inputs", "repetitions": 2})
    rows = []
    for index, probe in enumerate(probes, 1):
        row = {"family": probe["family"], "sha256": probe["sha256"],
               "origins": probe["origins"], "variants": []}
        good = probe["variants"][0]["result"]
        for variant in probe["variants"]:
            label = variant["variant"]
            truth = label == "repaired"
            kind = "residual" if label == "residual" else "historical"
            repetitions = []
            for _ in range(2):
                workspace = ContractWorkspace(probe["family"], truth, probe["image"], kind)
                try:
                    if workspace.hashes() != variant["source_sha256"]:
                        raise ValueError(f"Source mismatch: {index}/{label}")
                    repetitions.append(workspace.execute(["python", "-"], probe["code"]))
                finally:
                    workspace.close()
            comparable = all(usable(r) for r in repetitions)
            bad = variant["result"]
            row["variants"].append({
                "variant": label, "repetitions": repetitions,
                "repeat_comparable": comparable,
                "repeat_differs": comparable and signature(repetitions[0]) != signature(
                    repetitions[1]),
                "normalized_repeat_differs": comparable and normalized_signature(
                    repetitions[0]) != normalized_signature(repetitions[1]),
                "archived_differential": label != "repaired" and usable(good) and usable(bad)
                and signature(good) != signature(bad),
                "archived_address_only_difference": label != "repaired"
                and usable(good) and usable(bad) and signature(good) != signature(bad)
                and normalized_signature(good) == normalized_signature(bad),
            })
        write_once(run / f"probe-{index:03d}.json", row)
        rows.append(row)
        print(json.dumps({"finished": index, "total": len(probes),
                          "nonrepeatable": any(v["repeat_differs"] for v in row["variants"])}),
              flush=True)
    variants = [v for r in rows for v in r["variants"]]
    summary = {
        "probes": len(rows), "variant_pairs": len(variants),
        "executions": 2*len(variants),
        "noncomparable_variant_pairs": sum(not v["repeat_comparable"] for v in variants),
        "nonrepeatable_variant_pairs": sum(v["repeat_differs"] for v in variants),
        "nonrepeatable_probes": sum(any(v["repeat_differs"] for v in r["variants"]) for r in rows),
        "address_only_archived_differences": sum(
            v["archived_address_only_difference"] for v in variants),
        "archived_differential_comparisons": sum(v["archived_differential"] for v in variants),
        "status": "completed", "model_inference": False,
    }
    write_once(run / "completion.json", summary)
    archive.seal(EXPERIMENT + ".run", run, kind="run", title="Identical-source replay controls",
                 experiment=EXPERIMENT, parents=[EXPERIMENT + ".inputs"])
    archive.build_index()
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
