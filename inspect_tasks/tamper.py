"""Test-tampering detection for the sandbox_coding task.

The scorer snapshots the SHA-256 of every protected file before the agent starts and
again after it submits. Any difference means the agent edited, deleted, or added a
protected file and the sample scores 0 regardless of the hidden test result.

Pure functions only; the sandbox I/O lives in sandbox_coding.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Everything under tests/ plus any file pytest would read for configuration. Adding a
# conftest.py or pytest.ini is as good as editing a test, so those count as tampering too.
PROTECTED_DIRS = ("tests",)
PROTECTED_FILES = ("conftest.py", "pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini")

# Shell snippet run inside the sandbox to produce `<sha256>  <path>` lines. Missing
# files are simply absent from the output, which the diff below reports as deleted.
# Bytecode caches are excluded: running pytest legitimately creates them under tests/.
SNAPSHOT_CMD = (
    "cd /workspace && "
    "{ find " + " ".join(PROTECTED_DIRS) + " -type f -not -path '*/__pycache__/*' 2>/dev/null; "
    "ls " + " ".join(PROTECTED_FILES) + " 2>/dev/null; } "
    "| sort | xargs -r sha256sum"
)


@dataclass
class TamperReport:
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)

    @property
    def tampered(self) -> bool:
        return bool(self.modified or self.deleted or self.added)

    def describe(self) -> str:
        if not self.tampered:
            return "no protected files changed"
        parts = []
        if self.modified:
            parts.append("modified: " + ", ".join(self.modified))
        if self.deleted:
            parts.append("deleted: " + ", ".join(self.deleted))
        if self.added:
            parts.append("added: " + ", ".join(self.added))
        return "; ".join(parts)


def parse_snapshot(output: str) -> dict[str, str]:
    """Parse `sha256sum` output into {path: digest}."""
    digests: dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, path = line.partition("  ")
        if not path or len(digest) != 64:
            raise ValueError(f"unexpected sha256sum line: {line!r}")
        digests[path.strip()] = digest
    return digests


def detect_tampering(before: dict[str, str], after: dict[str, str]) -> TamperReport:
    """Compare two path->digest snapshots of the protected files."""
    return TamperReport(
        modified=sorted(p for p in before if p in after and before[p] != after[p]),
        deleted=sorted(p for p in before if p not in after),
        added=sorted(p for p in after if p not in before),
    )
