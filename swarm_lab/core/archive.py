"""Write-once research bundles, immutable inventory records and a derived index."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,160}\Z")
OBJECTS = "research/archive/objects"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_once(path, value):
    path = Path(path)
    encoded = (value if isinstance(value, str)
               else json.dumps(value, indent=2, allow_nan=False) + "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())


class Archive:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.registry = self.root / "research/registry"
        (self.registry / "bundles").mkdir(parents=True, exist_ok=True)
        (self.registry / "packs").mkdir(parents=True, exist_ok=True)

    def path(self, value):
        path = self.root / value
        if path.is_symlink() or not path.resolve().is_relative_to(self.root / "research"):
            raise ValueError("Bundle must be inside research and cannot be a symlink")
        return path.resolve()

    def records(self):
        paths = sorted((self.registry / "bundles").glob("*.json"))
        return [json.loads(p.read_text()) for p in paths]

    def inventory(self, value):
        path = self.path(value)
        if not path.exists():
            raise FileNotFoundError(path)
        files = [path] if path.is_file() else sorted(path.rglob("*"))
        if any(p.is_symlink() for p in files):
            raise ValueError("Symlinks cannot be archived")
        return {p.relative_to(self.root).as_posix(): digest(p)
                for p in files if p.is_file()}

    def seal(self, bundle_id, path, *, kind, title, experiment, parents=(), legacy=False,
             original_path=None):
        if not ID.fullmatch(bundle_id):
            raise ValueError("Invalid bundle identifier")
        path = self.path(path)
        if path.is_relative_to(self.registry):
            raise ValueError("The registry cannot archive itself")
        with (self.registry / ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            records = self.records()
            known = {r["id"] for r in records}
            relative = path.relative_to(self.root).as_posix()
            if bundle_id in known or any(r["path"] == relative for r in records):
                raise FileExistsError("This bundle ID or path is already sealed")
            if any(path.is_relative_to(self.root / r["path"])
                   or (self.root / r["path"]).is_relative_to(path) for r in records):
                raise FileExistsError("Bundle overlaps already sealed evidence")
            if any(parent not in known for parent in parents):
                raise ValueError("Unknown parent bundle")
            record = {
                "schema": "witness.research-bundle.v1", "id": bundle_id, "kind": kind,
                "title": title, "experiment": experiment, "path": relative,
                "parents": list(parents), "legacy_registration": legacy,
                "original_path": original_path,
                "sealed_at": datetime.now(UTC).isoformat(),
                "files": self.inventory(relative),
                "scope": "Detects subsequent file changes/additions/deletions. A legacy "
                "registration is a baseline taken now, not proof of prior immutability.",
            }
            write_once(self.registry / "bundles" / f"{bundle_id}.json", record)
        return record

    def create_experiment(self, experiment_id, title, question, protocol):
        if not ID.fullmatch(experiment_id):
            raise ValueError("Invalid experiment identifier")
        folder = self.root / "research/experiments" / experiment_id
        folder.mkdir(parents=True, exist_ok=False)
        design = folder / "design"
        write_once(design / "experiment.json", {
            "id": experiment_id, "title": title, "question": question,
            "created_at": datetime.now(UTC).isoformat()})
        write_once(design / "protocol.md", protocol)
        self.seal(experiment_id + ".design", design, kind="design", title=title,
                  experiment=experiment_id)
        return folder

    def new_bundle(self, experiment_id, kind, bundle_id):
        if kind not in ("runs", "analyses", "reports", "adjudications", "gates"):
            raise ValueError("Unknown bundle kind")
        if not ID.fullmatch(bundle_id) or not ID.fullmatch(experiment_id):
            raise ValueError("Invalid identifier")
        folder = self.root / "research/experiments" / experiment_id
        if not (folder / "design/experiment.json").is_file():
            raise ValueError("Experiment must be registered first")
        target = folder / kind / bundle_id
        target.mkdir(parents=True, exist_ok=False)
        return target

    def audit(self):
        errors = []
        records = self.records()
        known = {r["id"] for r in records}
        try:
            packed = self.packed()
        except ValueError as exc:
            return {"bundles": len(records), "files": 0, "errors": [{"error": str(exc)}]}
        verified = {sha: self.object_ok(sha) for sha in set(packed.values())}
        sealed = {name for r in records for name in r["files"]}
        errors.extend({"id": "pack", "error": "Packed file is not sealed", "path": name}
                      for name in sorted(set(packed) - sealed))
        for record in records:
            try:
                try:
                    actual = self.inventory(record["path"])
                except FileNotFoundError:
                    actual = {}
                for name, sha in record["files"].items():
                    if name not in actual and packed.get(name) == sha and verified[sha]:
                        actual[name] = sha
                if actual != record["files"]:
                    errors.append({"id": record["id"], "changed_or_missing": [
                        p for p, value in record["files"].items() if actual.get(p) != value],
                        "added": sorted(set(actual)-set(record["files"]))})
                if any(p not in known for p in record["parents"]):
                    errors.append({"id": record["id"], "error": "Missing parent bundle"})
            except (ValueError, FileNotFoundError) as exc:
                errors.append({"id": record["id"], "error": type(exc).__name__})
        return {"bundles": len(records), "files": sum(len(r["files"]) for r in records),
                "packed_files": len(packed), "objects": len(verified), "errors": errors}

    # Content-addressed packing. Sealed snapshot files that repeat across runs are moved
    # into research/archive/objects/<sha256>, recorded by write-once pack records. The
    # audit treats a packed file as present when its object exists with the sealed hash,
    # and restore rebuilds the original paths byte for byte.

    def object_path(self, sha):
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("Invalid object hash")
        return self.root / OBJECTS / sha[:2] / sha

    def packs(self):
        return [json.loads(p.read_text()) for p in sorted((self.registry / "packs").glob("*.json"))]

    def packed(self):
        mapping = {}
        for record in self.packs():
            for name, sha in record["files"].items():
                if mapping.setdefault(name, sha) != sha:
                    raise ValueError(f"Conflicting pack records for {name}")
        return mapping

    def object_ok(self, sha):
        path = self.object_path(sha)
        return path.is_file() and not path.is_symlink() and digest(path) == sha

    def read_bytes(self, relative):
        """Bytes of a research file, from disk or from the object store if packed."""
        relative = Path(relative).as_posix()
        path = self.root / relative
        if path.is_file():
            return path.read_bytes()
        sha = self.packed().get(relative)
        if sha is None or not self.object_ok(sha):
            raise FileNotFoundError(relative)
        return self.object_path(sha).read_bytes()

    def pack(self, pack_id, folders):
        """Move every file under the given sealed folders into the object store."""
        if not ID.fullmatch(pack_id):
            raise ValueError("Invalid pack identifier")
        sealed = {}
        for record in self.records():
            sealed.update(record["files"])
        files = {}
        for folder in folders:
            folder = self.path(folder)
            for path in sorted(folder.rglob("*")):
                if path.is_symlink():
                    raise ValueError("Symlinks cannot be packed")
                if not path.is_file():
                    continue
                name = path.relative_to(self.root).as_posix()
                sha = digest(path)
                if sealed.get(name) != sha:
                    raise ValueError(f"Only sealed, unchanged files can be packed: {name}")
                files[name] = sha
        if not files:
            raise ValueError("Nothing to pack")
        with (self.registry / ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            already = self.packed()
            if any(name in already for name in files):
                raise FileExistsError("A file in this set is already packed")
            for name, sha in files.items():
                target = self.object_path(sha)
                if target.exists():
                    if not self.object_ok(sha):
                        raise ValueError(f"Corrupt existing object {sha}")
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as stream:
                        stream.write((self.root / name).read_bytes())
                        stream.flush()
                        os.fsync(stream.fileno())
                if target.read_bytes() != (self.root / name).read_bytes():
                    raise ValueError(f"Object differs from original: {name}")
            record = {"schema": "witness.pack.v1", "id": pack_id,
                      "objects": OBJECTS, "packed_at": datetime.now(UTC).isoformat(),
                      "files": files}
            write_once(self.registry / "packs" / f"{pack_id}.json", record)
            for name in files:
                (self.root / name).unlink()
            for folder in folders:
                folder = self.root / folder
                for path in sorted(folder.rglob("*"), reverse=True):
                    if path.is_dir() and not any(path.iterdir()):
                        path.rmdir()
                if folder.is_dir() and not any(folder.iterdir()):
                    folder.rmdir()
        return record

    def restore(self, prefix="research/", destination=None):
        """Rebuild packed files under a path prefix. Never overwrites an existing file."""
        destination = Path(destination) if destination else self.root
        restored = []
        for name, sha in sorted(self.packed().items()):
            if not name.startswith(prefix):
                continue
            if not self.object_ok(sha):
                raise ValueError(f"Missing or corrupt object for {name}")
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(self.object_path(sha).read_bytes())
            if digest(target) != sha:
                raise ValueError(f"Restored bytes differ for {name}")
            restored.append(name)
        return restored
    def build_index(self):
        records = self.records()
        lines = ["# Witness experiment index", "",
                 "Generated from write-once bundle records. This index is replaceable; "
                 "registered evidence is not.", "",
                 "Completed runs, frozen designs, analyses, report editions and corrections "
                 "have separate records. Original paths remain intact.", "",
                 "| Experiment | Kind | Title / files | Bundle ID |",
                 "| --- | --- | --- | --- |"]
        for record in sorted(records, key=lambda r: (r["experiment"], r["sealed_at"], r["id"])):
            path = self.path(record["path"])
            if path.is_dir():
                for name in ("report.md", "protocol.md", "manifest.json", "completion.json"):
                    if (path / name).is_file():
                        path /= name
                        break
            link = Path("..") / path.relative_to(self.root / "research")
            title = record["title"].replace("|", "\\|")
            original = record.get("original_path")
            suffix = (f" ([living original](../../{Path(original).as_posix()}))"
                      if original and (self.root / original).is_file() else "")
            lines.append(f"| {record['experiment']} | {record['kind']} | "
                         f"[{title}]({link.as_posix()}){suffix} | {record['id']} |")
        (self.registry / "index.md").write_text("\n".join(lines) + "\n")
        (self.registry / "index.json").write_text(json.dumps(records, indent=2) + "\n")


def bootstrap_legacy(root):
    archive = Archive(root)
    existing = {r["id"] for r in archive.records()}
    for group in ("swarm", "agent-study", "portfolio", "pilots"):
        base = archive.root / "research" / group
        if not base.exists():
            continue
        for manifest in sorted(base.glob("*/manifest.json")):
            folder = manifest.parent
            bundle_id = f"legacy-{group}-{folder.name}"
            if bundle_id not in existing:
                archive.seal(bundle_id, folder, kind="run", title=folder.name,
                             experiment="legacy-" + group, legacy=True)
        for doc in sorted(base.glob("*.md")):
            # Preserve the current edition; living source summaries may later be revised.
            bundle_id = f"legacy-{group}-{doc.stem}-doc-{digest(doc)[:12]}"
            if bundle_id in existing:
                continue
            copy = archive.root / "research/archive/legacy-writeups" / group / (
                doc.stem + "-" + digest(doc)[:12] + ".md")
            copy.parent.mkdir(parents=True, exist_ok=True)
            with copy.open("xb") as stream:
                stream.write(doc.read_bytes())
            archive.seal(bundle_id, copy, kind="writeup",
                         title=f"{group}/{doc.name} (archived edition)",
                         experiment="legacy-" + group, legacy=True,
                         original_path=doc.relative_to(archive.root).as_posix())
        # Loose analyses and reference gates were historically replaceable files.
        # Preserve their exact current editions too, without freezing live ledgers.
        for source in sorted(base.iterdir()):
            if (not source.is_file() or source.suffix not in (".json", ".jsonl", ".py")
                    or source.name in ("budget.jsonl", "pilot-budget.jsonl")):
                continue
            bundle_id = f"legacy-{group}-{source.stem}-artifact-{digest(source)[:12]}"
            if bundle_id in existing:
                continue
            copy = archive.root / "research/archive/legacy-artifacts" / group / (
                source.stem + "-" + digest(source)[:12] + source.suffix)
            copy.parent.mkdir(parents=True, exist_ok=True)
            with copy.open("xb") as stream:
                stream.write(source.read_bytes())
            archive.seal(bundle_id, copy, kind="analysis", title=f"{group}/{source.name}",
                         experiment="legacy-" + group, legacy=True,
                         original_path=source.relative_to(archive.root).as_posix())
        # Includes frozen vendor packages, counterexamples and efficiency source.
        for folder in sorted(base.iterdir()):
            if not folder.is_dir() or folder.name.startswith((".", "__")):
                continue
            if any((archive.root / r["path"]).is_relative_to(folder)
                   for r in archive.records()):
                continue
            archive.seal(f"legacy-{group}-{folder.name}-support", folder,
                         kind="support", title=f"{group}/{folder.name}",
                         experiment="legacy-" + group, legacy=True)
    archive.build_index()
    return archive.audit()
