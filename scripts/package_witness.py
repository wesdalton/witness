"""Build the public source archive from an explicit allowlist, never the working tree."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "website/dist/assets/witness-source.zip"
DIRECTORIES = (
    "swarm_lab",
    "website/dist",
    "website/tests",
    "website/scripts",
    "inspect_tasks",
    "sandbox",
    "tests",
    "data",
    "smoke",
)
FILES = (
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "pyproject.toml",
    "website/package.json",
    "scripts/package_witness.py",
    "scripts/build_site_data.py",
    "scripts/sandbox_scenarios.py",
    "research/pilots/scorer_integrity.py",
    "research/pilots/scorer_integrity_results.json",
    "research/swarm/protocol.md",
    "research/swarm/methods.md",
    "research/swarm/design.md",
    "research/swarm/pilot-plan.md",
    "research/swarm/pilot-report.md",
    "research/swarm/pilot-summary.json",
    "research/swarm/pilot-audit.json",
    "research/swarm/mechanistic-sweep.json",
    "research/swarm/scripted-smoke-release.json",
    "research/swarm/scripted-smoke-release.jsonl",
    "research/legacy-inspect-readme.md",
)
PILOT_RECORDS = (
    ("luna-calibration-01", "pytest_module_shadow-reports"),
    ("luna-pilot-seed42", "honest_fix-reports"),
    ("luna-honest-reports-attempt02", "honest_fix-reports"),
    ("luna-honest-reports-attempt03", "honest_fix-reports"),
    ("luna-paced-pair-seed42", "honest_fix-reports"),
    ("luna-paced-false-seed42", "pytest_module_shadow-reports"),
)
EXCLUDED_PARTS = {"__pycache__", "node_modules", ".git", ".openai", ".pytest_cache"}


def main():
    from build_site_data import build

    assets = ROOT / "website/dist/assets"
    assets.mkdir(parents=True, exist_ok=True)
    build()
    for source, target in [
        ("research/swarm/methods.md", "methods.md"),
        ("research/swarm/protocol.md", "research-protocol.md"),
        ("research/swarm/design.md", "design-notes.md"),
        ("research/swarm/pilot-report.md", "pilot-report.md"),
        ("research/swarm/pilot-summary.json", "pilot-summary.json"),
        ("research/swarm/pilot-audit.json", "pilot-audit.json"),
        ("research/pilots/scorer_integrity_results.json", "ledger-pilot.json"),
    ]:
        (assets / target).write_bytes((ROOT / source).read_bytes())
    paths = {ROOT / name for name in FILES}
    for folder, run in PILOT_RECORDS:
        for name in ("manifest.json", "completion.json", f"{run}.json", f"{run}.jsonl"):
            paths.add(ROOT / "research/swarm" / folder / name)
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
    for name in DIRECTORIES:
        paths.update((ROOT / name).rglob("*"))
    files = {}
    for path in sorted(paths):
        relative = path.relative_to(ROOT)
        if path == OUT or not path.is_file() or any(p in EXCLUDED_PARTS for p in relative.parts):
            continue
        if path.is_symlink() or path.suffix in {".pyc", ".env"} or path.name.startswith(".env"):
            raise ValueError(f"Refusing unexpected artifact: {relative}")
        files[relative.as_posix()] = path.read_bytes()
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    files["SOURCE_SHA256.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(f"witness-swarm-lab/{name}", (2026, 10, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    print(
        json.dumps(
            {
                "path": str(OUT),
                "files": len(files),
                "bytes": OUT.stat().st_size,
                "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
