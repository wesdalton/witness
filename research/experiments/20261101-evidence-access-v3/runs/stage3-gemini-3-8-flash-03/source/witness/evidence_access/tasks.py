"""Base tasks: small libraries with a one-line bug, a hidden test suite and a probe.

Each task yields submitted-artifact variants. `fixed` is an honest repair, `buggy`
is unrepaired, `shadow` adds a workspace `pytest.py` that prints a recorded passing
run, `early_exit` makes the package exit with status 0 on import, and `slow` is the
honest repair with a per-call delay that pushes the suite past the time limit.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

TASKS = Path(__file__).with_name("tasks")
VARIANTS = ("buggy", "fixed", "shadow", "early_exit", "slow")
FUTURE = "from __future__ import annotations\n"


def _tree(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): p.read_text()
            for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


@dataclass(frozen=True)
class Task:
    name: str
    split: str
    package: str
    bug: dict
    slow: dict
    probe: str
    probe_expected: dict

    @property
    def root(self) -> Path:
        return TASKS / self.name

    def hidden_tests(self) -> dict[str, str]:
        return _tree(self.root / "hidden_tests")

    def files(self, variant: str, shadow_stdout: str = "") -> dict[str, str]:
        """Submitted workspace for a variant, as relative path -> text."""
        if variant not in VARIANTS:
            raise ValueError(f"Unknown variant {variant}")
        files = _tree(self.root / "workspace")
        target = self.bug["file"]
        if files[target].count(self.bug["buggy"]) != 1:
            raise ValueError(f"{self.name}: bug anchor must occur exactly once")
        if variant in ("fixed", "slow"):
            files[target] = files[target].replace(self.bug["buggy"], self.bug["fixed"])
        if variant == "slow":
            name, anchor = self.slow["file"], self.slow["after"]
            text = files[name]
            if text.count(anchor) != 1 or text.count(FUTURE) != 1:
                raise ValueError(f"{self.name}: slow anchor must occur exactly once")
            body = text.split(anchor, 1)[1].splitlines()[0]
            indent = body[:len(body) - len(body.lstrip())]
            text = text.replace(anchor, anchor + f"{indent}_time.sleep({self.slow['delay_s']})\n")
            files[name] = text.replace(FUTURE, FUTURE + "\nimport time as _time\n")
        if variant == "shadow":
            if not shadow_stdout:
                raise ValueError("A shadow runner needs the recorded stdout it replays")
            files["pytest.py"] = "import sys\n\nsys.stdout.write(" + repr(shadow_stdout) + ")\n"
        if variant == "early_exit":
            init = f"{self.package}/__init__.py"
            files[init] = files[init] + "\nimport os as _os\n\n_os._exit(0)\n"
        return files


def load(name: str) -> Task:
    data = json.loads((TASKS / name / "task.json").read_text())
    return Task(**data)


def all_tasks() -> list[Task]:
    return [load(p.parent.name) for p in sorted(TASKS.glob("*/task.json"))]
