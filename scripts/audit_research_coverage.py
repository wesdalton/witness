"""Check that research evidence is fully registered and the budget ledger is append-only.

Two checks, no network access:
- every file under research/experiments/ belongs to a sealed bundle, and every sealed
  bundle still matches its inventory (Archive.audit);
- each committed edition of research/budget.jsonl, following its earlier path, is a
  byte prefix of the current file, so rows can be appended but never edited or removed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from witness.core.archive import Archive  # noqa: E402

EXPERIMENTS = "research/experiments"
LEDGER = "research/budget.jsonl"
# Before November 2026 the ledger lived here; its history is checked under either name.
FORMER_LEDGER_PATHS = ("research/agent-study/budget.jsonl",)


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True)


def unregistered(root: Path, archive: Archive) -> list[str]:
    sealed = {name for r in archive.records() for name in r["files"]}
    base = root / EXPERIMENTS
    files = sorted(base.rglob("*")) if base.is_dir() else []
    return [name for path in files
            if path.is_file() and "__pycache__" not in path.parts
            and (name := path.relative_to(root).as_posix()) not in sealed]


def committed_editions(root: Path) -> list[tuple[str, bytes]] | None:
    """(commit:path, bytes) for each committed ledger edition; None outside a git work tree."""
    inside = git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != b"true":
        return None
    seen, editions = set(), []
    for path in (LEDGER, *FORMER_LEDGER_PATHS):
        log = git(root, "log", "--follow", "--name-only", "--format=commit %H", "--", path)
        if log.returncode != 0:
            continue
        commit = None
        for line in log.stdout.decode().splitlines():
            if line.startswith("commit "):
                commit = line.split()[1]
            elif line.strip() and commit and (commit, line.strip()) not in seen:
                seen.add((commit, line.strip()))
                shown = git(root, "show", f"{commit}:{line.strip()}")
                if shown.returncode == 0:
                    editions.append((f"{commit[:12]}:{line.strip()}", shown.stdout))
    return editions


def ledger_check(root: Path, editions: list[tuple[str, bytes]] | None = None) -> dict:
    """Every earlier edition must be a byte prefix of the current ledger."""
    if editions is None:
        editions = committed_editions(root)
    current = root / LEDGER
    result = {"path": LEDGER, "present": current.is_file(), "git_history": editions is not None,
              "editions_checked": 0, "rewritten_editions": []}
    if not current.is_file() or editions is None:
        return result
    raw = current.read_bytes()
    for label, earlier in editions:
        result["editions_checked"] += 1
        if not raw.startswith(earlier):
            result["rewritten_editions"].append(label)
    return result


def coverage(root: Path) -> dict:
    archive = Archive(root)
    ledger = ledger_check(root)
    return {
        "schema": "witness.archive-coverage.v2",
        "unregistered": unregistered(root, archive),
        "ledger": ledger,
        "integrity": archive.audit(),
        "scope": "Files under research/experiments/ and the budget ledger's committed "
        "history. Does not prove immutability before registration or establish an "
        "off-machine backup. Outside a git work tree the ledger history is not checked.",
    }


def failed(result: dict) -> bool:
    ledger = result["ledger"]
    return bool(result["unregistered"] or result["integrity"]["errors"]
                or not ledger["present"] or ledger["rewritten_editions"])


def main() -> int:
    result = coverage(ROOT)
    print(json.dumps(result, indent=2))
    return int(failed(result))


if __name__ == "__main__":
    raise SystemExit(main())
