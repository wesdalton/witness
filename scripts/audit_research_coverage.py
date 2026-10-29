"""Check coverage of on-disk research evidence, including ignored historical logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab.core.archive import Archive, digest  # noqa: E402

LEDGERS = {"research/agent-study/budget.jsonl", "research/swarm/pilot-budget.jsonl"}


def candidates(root):
    files = []
    for base in (root / "research", root / "logs"):
        for path in sorted(base.rglob("*")):
            relative = path.relative_to(root)
            if (not path.is_file() or "__pycache__" in relative.parts
                    or relative.parts[:2] in (("research", "archive"), ("research", "registry"))):
                continue
            files.append(path)
    return files


def coverage(root):
    archive = Archive(root)
    records = archive.records()
    sealed = {name for r in records for name in r["files"]}
    originals = defaultdict(list)
    for record in records:
        if record.get("original_path"):
            originals[record["original_path"]].append(record)
    missing, changed, prefixes = [], [], []
    paths = candidates(root)
    for path in paths:
        name = path.relative_to(root).as_posix()
        if name in sealed:
            continue
        editions = originals[name]
        if not editions:
            missing.append(name)
            continue
        if name in LEDGERS:
            raw = path.read_bytes()
            if all(raw.startswith((root / r["path"]).read_bytes()) for r in editions):
                prefixes.append(name)
            else:
                changed.append(name)
        elif not any(digest(path) in r["files"].values() for r in editions):
            changed.append(name)
    return {"schema": "witness.archive-coverage.v1", "files_checked": len(paths),
            "unregistered": missing, "changed_unarchived_editions": changed,
            "append_only_ledgers_checked": prefixes, "integrity": archive.audit(),
            "scope": "Files currently present under this repository's research/ and logs/. "
            "Excludes archive/index duplicates and Python caches. Does not reconstruct lost "
            "history, prove prior immutability, or establish an off-machine backup."}


def capture_legacy(root):
    archive = Archive(root)
    records = archive.records()
    originals = {(r.get("original_path"), h) for r in records for h in r["files"].values()}
    selected = list((root / "research").glob("*.md"))
    selected += [p for p in (root / "logs").rglob("*") if p.is_file()]
    selected += [root / name for name in LEDGERS if (root / name).is_file()]
    sealed = {name for r in records for name in r["files"]}
    for path in sorted(selected):
        name = path.relative_to(root).as_posix()
        sha = digest(path)
        if name in sealed or (name, sha) in originals:
            continue
        path_id = hashlib.sha256(name.encode()).hexdigest()[:12]
        bundle_id = f"recovered-{path_id}-{sha[:12]}"
        target = root / "research/archive/recovered" / (bundle_id + path.suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(path.read_bytes())
        kind = "ledger-snapshot" if name in LEDGERS else "inspect-log" if (
            path.suffix == ".eval") else "legacy-artifact"
        archive.seal(bundle_id, target, kind=kind, title=name,
                     experiment="legacy-recovered", original_path=name, legacy=True)
    archive.build_index()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-legacy", action="store_true")
    args = parser.parse_args()
    if args.capture_legacy:
        capture_legacy(ROOT)
    result = coverage(ROOT)
    print(json.dumps(result, indent=2))
    return bool(result["unregistered"] or result["changed_unarchived_editions"]
                or result["integrity"]["errors"])


if __name__ == "__main__":
    raise SystemExit(main())
