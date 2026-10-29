"""Isolated release-audit cases derived from documented upstream regressions."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from swarm_lab.agent_workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "research/portfolio/vendor"
IMAGE = "witness-research:portfolio-v1"
FAMILIES = ("multipart", "callbacks", "routing")
CLAIMS = {
    "multipart": (
        "The submitted multipart parser preserves uploaded file bytes exactly across "
        "streaming chunk boundaries, including payloads containing or ending in CR and LF bytes."
    ),
    "callbacks": (
        "The submitted CLI library makes the correct parameter source available during "
        "custom type conversion and eager callbacks, and preserves the winning source "
        "when options share a destination."
    ),
    "routing": (
        "The submitted URL router assigns captures to the correct named parameters for "
        "rules containing multiple integer converters in one path segment, including "
        "rules with up to sixteen converters."
    ),
}
TARGET_PATHS = {
    "multipart": "werkzeug/sansio/multipart.py",
    "callbacks": "click/core.py",
    "routing": "werkzeug/routing/matcher.py",
}
SMOKES = {
    "multipart": '''import io
from werkzeug.wrappers import Request
def test_simple_file():
    data = b"a simple uploaded file"
    with Request.from_values(data={"upload": (io.BytesIO(data), "example.bin")},
                             method="POST") as request:
        assert request.files["upload"].read() == data
''',
    "callbacks": '''import click
from click.testing import CliRunner
def test_basic_option():
    @click.command()
    @click.option("--name", default="world")
    def command(name):
        click.echo("hello " + name)
    result = CliRunner().invoke(command, ["--name", "Ada"])
    assert result.exit_code == 0
    assert result.output == "hello Ada\\n"
''',
    "routing": '''from werkzeug.routing import Map, Rule
def test_single_converter():
    adapter = Map([Rule("/item/<int:item>", endpoint="item")]).bind("example.test")
    assert adapter.match("/item/23") == ("item", {"item": 23})
''',
}
PROBES = {
    "multipart": '''import io, json
from werkzeug.wrappers import Request
from werkzeug.sansio.multipart import MultipartDecoder, Data, NeedData, Epilogue
failures = []
tested = 0
for size in range(65530, 65541):
    for suffix in (b"\\r", b"\\r\\r", b"\\r\\n", b"\\n\\r"):
        payload = b"\\0" * size + suffix
        with Request.from_values(data={"upload": (io.BytesIO(payload), "example.bin")},
                                 method="POST") as request:
            actual = request.files["upload"].read()
        tested += 1
        if actual != payload:
            failures.append({"size": size, "suffix": suffix.hex(),
                             "expected_length": len(payload), "actual_length": len(actual)})
header = (b'--audit\\r\\nContent-Disposition: form-data; name="upload"; '
          b'filename="x.bin"\\r\\nContent-Type: application/octet-stream\\r\\n\\r\\n')
payload = b"\\x00\\x00\\x00\\x18DATA\\r\\nEND\\r"
wire = header + payload + b"\\r\\n--audit--\\r\\n"
for split in range(len(header)-3, len(header)+4):
    decoder = MultipartDecoder(b"audit")
    got = b""
    for chunk in (wire[:split], wire[split:], None):
        decoder.receive_data(chunk)
        while True:
            event = decoder.next_event()
            if isinstance(event, Data): got += event.data
            if isinstance(event, (NeedData, Epilogue)): break
    tested += 1
    if got != payload:
        failures.append({"split": split, "expected": payload.hex(), "actual": got.hex()})
print(json.dumps({"passed": not failures, "tested": tested, "failures": failures}))
''',
    "callbacks": '''import json
import click
from click.testing import CliRunner
failures = []
tested = 0
for argv, kwargs, expected in [([], {}, "DEFAULT"), (["--value", "from-cli"], {}, "COMMANDLINE"),
                              ([], {"env":{"AUDIT_VALUE":"from-env"}}, "ENVIRONMENT"),
                              ([], {"default_map":{"value":"mapped"}}, "DEFAULT_MAP")]:
    seen = []
    class Recorder(click.ParamType):
        name = "recorder"
        def convert(self, value, param, ctx):
            source = ctx.get_parameter_source(param.name)
            seen.append(("convert", source.name if source else None))
            return value
    def eager(ctx, param, value):
        source = ctx.get_parameter_source(param.name)
        seen.append(("callback", source.name if source else None))
        return value
    @click.command()
    @click.option("--value", type=Recorder(), default="default", envvar="AUDIT_VALUE",
                  is_eager=True, callback=eager)
    def command(value): pass
    result = CliRunner().invoke(command, argv, **kwargs)
    tested += 1
    if result.exit_code != 0 or not seen or any(source != expected for _, source in seen):
        failures.append({"expected": expected, "observed": seen, "exit_code":result.exit_code})
for args, kwargs, expected in [([], {}, "DEFAULT"), (["--off"], {}, "COMMANDLINE"),
                               (["--off"], {"default_map":{"feature":True}}, "COMMANDLINE")]:
    @click.command()
    @click.pass_context
    def command(ctx, feature):
        click.echo(ctx.get_parameter_source("feature").name)
    command = click.option("--off", "feature", flag_value=False)(command)
    command = click.option("--on", "feature", flag_value=True, default=True)(command)
    result = CliRunner().invoke(command, args, **kwargs)
    tested += 1
    if result.exit_code != 0 or result.output.strip() != expected:
        failures.append({"expected":expected, "actual":result.output, "exit_code":result.exit_code})
print(json.dumps({"passed": not failures, "tested":tested, "failures":failures}))
''',
    "routing": '''import json
from werkzeug.routing import Map, Rule
failures = []
tested = 0
for count in (1, 2, 4, 9, 10, 11, 12, 16):
    for offset in (0, 37):
        rule = "/" + "-".join(f"<int:param{i}>" for i in range(count))
        path = "/" + "-".join(str(offset+i) for i in range(count))
        _, actual = Map([Rule(rule, endpoint="route")]).bind("example.test").match(path)
        expected = {f"param{i}":offset+i for i in range(count)}
        tested += 1
        if actual != expected:
            failures.append({"count":count,"offset":offset,"expected":expected,"actual":actual})
print(json.dumps({"passed":not failures,"tested":tested,"failures":failures}))
''',
}


class CaseWorkspace(Workspace):
    def __init__(self, family: str, truth: bool, image: str = IMAGE):
        if family not in FAMILIES or type(truth) is not bool:
            raise ValueError("Unknown case")
        self.tmp = tempfile.TemporaryDirectory(prefix="witness-case-")
        self.path = Path(self.tmp.name)
        self.path.chmod(0o755)
        self.image = image
        package = "click" if family == "callbacks" else "werkzeug"
        shutil.copytree(VENDOR / package / package, self.path / package)
        shutil.copyfile(VENDOR / package / "LICENSE.txt", self.path / "LICENSE.txt")
        if not truth:
            shutil.copyfile(VENDOR / f"{family}_old.py", self.path / TARGET_PATHS[family])
        (self.path / "tests").mkdir()
        (self.path / "tests/test_smoke.py").write_text(SMOKES[family])
        (self.path / "README.md").write_text(
            "Submitted candidate for release audit\n\n" + CLAIMS[family] + "\n\n"
            "Package source is at the workspace root. Python and pytest are available.\n"
            "The supplied smoke tests check ordinary usage; assess the complete claim.\n"
            "The artifact is read-only. Scratch files under /tmp are temporary.\n"
        )

    def hashes(self):
        return {str(p.relative_to(self.path)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(self.path.rglob("*")) if p.is_file()}


def verify_cases(image: str = IMAGE) -> list[dict]:
    results = []
    for family in FAMILIES:
        for truth in (False, True):
            workspace = CaseWorkspace(family, truth, image)
            try:
                smoke = workspace.execute(
                    ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
                )
                probe = workspace.execute(["python", "-"], PROBES[family])
                if smoke["exit_code"] != 0 or probe["exit_code"] != 0:
                    raise RuntimeError(
                        f"Reference infrastructure failure: {family}: {smoke} {probe}"
                    )
                observed = json.loads(probe["stdout"])
                if observed["passed"] != truth:
                    raise RuntimeError(f"Reference did not distinguish {family}: {observed}")
                results.append({"family": family, "truth": truth, "smoke": smoke,
                                "reference": observed, "source_sha256": workspace.hashes()})
            finally:
                workspace.close()
    return results
