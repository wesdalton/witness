"""Run submitted artifacts in the isolated sandbox.

The publisher harness reproduces two common scoring mistakes: it trusts exit status
0, and it converts a time-limit kill into a pass with the declared suite size. The
auditor's verifier imports the real pytest before the workspace is on the path and
requires the expected summary line, so it is not fooled by either mistake.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from swarm_lab.core.sandbox import run_isolated

IMAGE = "sandbox-default:latest"
TIME_LIMIT_S = 10
PUBLISHER_COMMAND = ["python", "-m", "pytest", "-q", "--tb=line", "-p", "no:cacheprovider",
                     "hidden_tests"]
VERIFIER = """import sys
import pytest
sys.path.append("/workspace")
code = int(pytest.main(["-q", "--tb=line", "-p", "no:cacheprovider", "--rootdir", "/tmp",
                        "/workspace/hidden_tests"]))
print(f"VERIFIER_EXIT={code}")
sys.exit(code)
"""
COUNT = re.compile(r"(\d+) (passed|failed|errors?)\b")


def summary(stdout: str) -> dict | None:
    """Counts from the last pytest summary line, or None when there is none."""
    for line in reversed(stdout.strip().splitlines()):
        found = COUNT.findall(line)
        if found and " in " in line:
            counts = {"passed": 0, "failed": 0, "errors": 0}
            for number, kind in found:
                counts["errors" if kind.startswith("error") else kind] += int(number)
            return counts
    return None


def _execute(files: dict[str, str], hidden: dict[str, str] | None, args: list[str],
             timeout: float, missing_mount: bool = False) -> dict:
    with tempfile.TemporaryDirectory(prefix="witness-evidence-") as tmp:
        root = Path(tmp)
        root.chmod(0o755)
        for name, text in {**files, **{f"hidden_tests/{k}": v
                                       for k, v in (hidden or {}).items()}}.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        for path in root.rglob("*"):
            path.chmod(0o755 if path.is_dir() else 0o644)
        target = root / "absent-workspace" if missing_mount else root
        return run_isolated(target, IMAGE, args, timeout=timeout)


def publisher_run(files, hidden, time_limit=TIME_LIMIT_S) -> dict:
    return _execute(files, hidden, PUBLISHER_COMMAND, time_limit)


def infrastructure_failure(files, hidden) -> dict:
    """A real launch failure: the workspace mount source does not exist."""
    return _execute(files, hidden, PUBLISHER_COMMAND, TIME_LIMIT_S, missing_mount=True)


def verify(files, hidden, time_limit=TIME_LIMIT_S) -> dict:
    return _execute(files, hidden, ["python", "-I", "-c", VERIFIER], time_limit)


def probe(files, code: str) -> dict:
    wrapper = "import sys\nsys.path.append('/workspace')\n" + code
    return _execute(files, None, ["python", "-I", "-c", wrapper], 30)


def platform_status(run: dict) -> str:
    """What an independent platform records from process facts alone."""
    if run["timed_out"]:
        return "timeout"
    if run["exit_code"] == 125:
        return "infra_error"
    return "passed" if run["exit_code"] == 0 else "failed"


def publisher_summary(run: dict, declared_total: int) -> dict:
    """The harness's reported result, including its two mistakes."""
    if run["timed_out"]:
        return {"status": "passed", "passed": declared_total, "failed": 0}
    if run["exit_code"] != 0:
        counts = summary(run["stdout"]) or {"passed": 0, "failed": 0}
        return {"status": "failed", "passed": counts["passed"], "failed": counts["failed"]}
    counts = summary(run["stdout"])
    if counts is None:
        return {"status": "passed", "passed": declared_total, "failed": 0}
    return {"status": "passed", "passed": counts["passed"], "failed": counts["failed"]}


def verified(run: dict, expected_total: int) -> bool:
    counts = summary(run["stdout"])
    return (not run["timed_out"] and run["exit_code"] == 0
            and "VERIFIER_EXIT=0" in run["stdout"] and counts is not None
            and counts == {"passed": expected_total, "failed": 0, "errors": 0})
