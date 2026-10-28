"""DRAFT real-regression corpus builder; not downloaded or validated as of 2026-10-28.

Experiment setup was rejected by the automatic command guard. No corpus or paid
run exists. Do not treat these reference checks as executed or retry that blocked
setup. This module is retained as unfinished preparation, separate from results.
"""

from __future__ import annotations

import io
import json
import shutil
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlopen

from swarm_lab.agent_workspace import Workspace
from swarm_lab.research_archive import digest, write_once

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = "20261028-repository-audits-v1"
BASE = ROOT / "research/experiments" / EXPERIMENT
CORPUS = BASE / "gates/corpus-v1"
IMAGE = "sha256:9b8a0832dacfa344a2c91f116c5bd578277760a235e9018820ceb4068a8740cb"
CASES = {
    "conversion": {
        "repo": "python-attrs/attrs", "pr": 1328,
        "buggy": "53e632c5218b729da6ac37a35b4b68379dc18999",
        "fixed": "6fda0a4e086b56d7058855e4c15112c8f58de74c",
        "packages": ["attr", "attrs"],
        "scope": "Review attrs converter composition and assignment conversion. "
        "Ordinary converter functions accept one value. A converter list applies them "
        "in order. attrs.define normally converts both constructor inputs and later "
        "assignments. Context-aware Converter wrappers can request instance/field context. "
        "Use package docstrings as the API contract. Start with attr/converters.py, "
        "attr/setters.py and the related implementation in attr/_make.py.",
        "reference": """import attrs
@attrs.define
class C:
    value = attrs.field(converter=[int, lambda x: x + 1])
c = C('10')
assert c.value == 11
c.value = '20'
assert c.value == 21
""",
        "smoke": "import attrs\nassert attrs.converters.pipe(int, str)('7', None, None) == '7'\n",
    },
    "versions": {
        "repo": "pypa/packaging", "pr": 1097,
        "buggy": "65ed5e92673aaabbfbeafa9b70463ba41bbae9db",
        "fixed": "16f558722612e8ad637c37f11464d5de62c8bb33",
        "packages": ["packaging"],
        "scope": "Review packaging version specifier membership, particularly strict "
        "ordered comparisons. Version order follows PEP 440 (epoch, release, pre/dev/post "
        "and local components). >V excludes post-releases of V unless V is itself a "
        "post-release, and excludes local variants of V. <V excludes pre-releases of V "
        "unless V is itself a pre-release. Explicit prereleases=True enables candidate "
        "pre-releases subject to these operator rules. Use package docstrings for other "
        "API details. Start with packaging/specifiers.py and packaging/version.py.",
        "reference": """from packaging.specifiers import Specifier
for prefix in ('1.0a', '1.0b', '1.0rc', '1.0.dev', '1.0.post'):
    s = Specifier('>' + prefix + '1')
    assert s.contains(prefix + '2+local', prereleases=True)
    assert not s.contains(prefix + '1+local', prereleases=True)
""",
        "smoke": "from packaging.specifiers import Specifier\nassert '2.0' in Specifier('>1.0')\n",
    },
    "streams": {
        "repo": "pallets/werkzeug", "pr": 3253,
        "buggy": "0aa1b95ae59f8ab9b4db8f4a1faabc996f7f5b8b",
        "fixed": "05ff3fe46845c8650e74c71b34f3f881392c478b",
        "packages": ["werkzeug"],
        "scope": "Review werkzeug.wsgi.LimitedStream's bounded binary I/O behavior. "
        "It wraps a binary input stream, limits consumption, tracks its position, and "
        "offers read/readinto. Follow the class docstrings for exhaustion, disconnects "
        "and max-limit semantics, and Python binary I/O conventions for byte counts and "
        "caller-owned buffers. Consider both BytesIO and conforming custom raw streams. "
        "Start with werkzeug/wsgi.py.",
        "reference": """from io import BytesIO
from werkzeug.wsgi import LimitedStream
class Short(BytesIO):
    def readinto(self, b):
        return super().readinto(memoryview(b)[:3])
for size in (8, 10, 17):
    stream = LimitedStream(Short(b'abcdefg'), 5)
    b = bytearray(b'x' * size)
    n = stream.readinto(b)
    assert n == 3
    assert b == bytearray(b'abc' + b'x' * (size - 3))
    assert stream.tell() == 3
""",
        "smoke": "from io import BytesIO\nfrom werkzeug.wsgi import LimitedStream\n"
        "assert LimitedStream(BytesIO(b'abc'), 2).read() == b'ab'\n",
    },
}


def fetch_corpus(destination=CORPUS):
    """One attempt per URL; exact commits, no installation or code execution."""
    for name, case in CASES.items():
        provenance = {k: v for k, v in case.items() if k not in ("reference", "smoke")}
        provenance["upstream_url"] = f"https://github.com/{case['repo']}/pull/{case['pr']}"
        for variant in ("buggy", "fixed"):
            sha = case[variant]
            url = f"https://codeload.github.com/{case['repo']}/tar.gz/{sha}"
            with urlopen(url, timeout=45) as response:
                raw = response.read(20_000_001)
            if len(raw) > 20_000_000:
                raise ValueError("Unexpected archive size")
            with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
                for member in archive.getmembers():
                    parts = Path(member.name).parts[1:]
                    if not member.isfile() or not parts or ".." in parts:
                        continue
                    selected = (len(parts) > 2 and parts[0] == "src"
                                and parts[1] in case["packages"])
                    license_file = len(parts) == 1 and parts[0].startswith("LICENSE")
                    if not selected and not license_file:
                        continue
                    relative = Path(*parts[1:]) if selected else Path(parts[0])
                    target = destination / name / variant / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as output:
                        output.write(archive.extractfile(member).read())
            provenance[variant + "_archive_url"] = url
        write_once(destination / name / "provenance.json", provenance)
        write_once(destination / name / "reference.py", case["reference"])
    write_once(destination / "inventory.json", {
        str(p.relative_to(destination)): digest(p)
        for p in sorted(destination.rglob("*")) if p.is_file()})


class RepoWorkspace(Workspace):
    def __init__(self, case, variant, corpus=CORPUS):
        self.tmp = tempfile.TemporaryDirectory(prefix="witness-repo-")
        self.path = Path(self.tmp.name)
        self.path.chmod(0o755)
        self.image = IMAGE
        for package in CASES[case]["packages"]:
            shutil.copytree(corpus / case / variant / package, self.path / package)

    def tool(self, name, arguments):
        if name == "read_file":
            path = (self.path / arguments["path"]).resolve()
            if not path.is_relative_to(self.path) or not path.is_file():
                return {"error": "Unavailable path"}
            start, end = arguments["start_line"], arguments["end_line"]
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= start+159:
                return {"error": "Request 1-160 lines, starting at line 1 or later"}
            lines = path.read_text().splitlines()
            return {"total_lines": len(lines), "text": "\n".join(
                f"{i+1}: {s}" for i, s in enumerate(lines) if start <= i+1 <= end)[:12000]}
        if name == "search":
            needle = arguments["text"]
            if not isinstance(needle, str) or not needle or len(needle) > 200:
                return {"error": "Search requires 1-200 literal characters"}
            matches = []
            for path in sorted(self.path.rglob("*.py")):
                for i, line in enumerate(path.read_text().splitlines(), 1):
                    if needle in line:
                        matches.append({"path": str(path.relative_to(self.path)),
                                        "line": i, "text": line[:250]})
                        if len(matches) == 40:
                            return {"matches": matches, "truncated": True}
            return {"matches": matches, "truncated": False}
        return super().tool(name, arguments)


def evaluate_tests(case, variant, tests):
    code = """import json, traceback
tests = json.loads(INPUT)
rows = []
for test in tests:
    try:
        exec(compile(test['code'], '<submitted-test>', 'exec'), {'__name__': '__main__'})
        rows.append({'name': test['name'], 'status': 'passed'})
    except Exception as exc:
        rows.append({'name': test['name'], 'status': 'failed',
                     'exception': type(exc).__name__, 'message': str(exc)[:600],
                     'traceback': traceback.format_exc()[-1400:]})
print('WITNESS_TEST_RESULTS=' + json.dumps(rows))
""".replace("INPUT", repr(json.dumps(tests)))
    workspace = RepoWorkspace(case, variant)
    try:
        result = workspace.execute(["python", "-"], code)
    finally:
        workspace.close()
    rows = None
    if not result["exit_code"] and not result["timed_out"] and not result["output_truncated"]:
        lines = [s for s in result["stdout"].splitlines() if s.startswith("WITNESS_TEST_RESULTS=")]
        if len(lines) == 1:
            rows = json.loads(lines[0].split("=", 1)[1])
    return {"execution": result, "tests": rows}


def reference_gate():
    rows = []
    for name, case in CASES.items():
        for variant in ("buggy", "fixed"):
            tests = [{"name": "smoke", "code": case["smoke"]},
                     {"name": "regression", "code": case["reference"]}]
            result = evaluate_tests(name, variant, tests)
            expected = ["passed", "failed" if variant == "buggy" else "passed"]
            passed = result["tests"] is not None and [
                t["status"] for t in result["tests"]] == expected
            rows.append({"case": name, "variant": variant, "passed": passed, **result})
    return {"passed": all(r["passed"] for r in rows), "rows": rows}
