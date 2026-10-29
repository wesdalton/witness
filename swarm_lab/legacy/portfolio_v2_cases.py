"""Regression contracts and locally repaired positives; v1 evidence stays immutable."""

from __future__ import annotations

import json

from swarm_lab.legacy.portfolio_cases import FAMILIES, IMAGE, PROBES, TARGET_PATHS, CaseWorkspace

CLAIMS = {
    "multipart": (
        "For a single uploaded file in a standard CRLF-delimited multipart body with "
        "complete valid Content-Disposition headers, parsing preserves payload bytes "
        "across chunk boundaries, including CR/LF payload bytes and boundaries split "
        "between either closing hyphen. The regression contract covers payloads over "
        "{ASCII a, CR, LF} of lengths 0 through 4, and zero-filled payloads near 64 KiB."
    ),
    "callbacks": (
        "For string-valued options, custom type conversion and eager callbacks observe "
        "the source of their current value: COMMANDLINE, ENVIRONMENT, DEFAULT_MAP, "
        "DEFAULT, or PROMPT, including initial processing inside interactive prompts. "
        "For two flags sharing a destination, the final source describes the winning value."
    ),
    "routing": (
        "For dash-separated paths with 1 through 16 named nonnegative integer converters "
        "in a single segment, each named parameter receives its corresponding input integer."
    ),
}

# Preserve potential boundary prefixes, including an incomplete closing marker.
MULTIPART_HELPER = r'''    def _last_partial_boundary_index(self, data: bytes | bytearray) -> int:
        markers = tuple(lb + b"--" + self.boundary for lb in (b"\r\n", b"\n", b"\r"))
        for found in re.finditer(rb"[\r\n]", data):
            start = found.start()
            available = len(data) - start
            for marker in markers:
                count = min(available, len(marker))
                if data[start:start + count] != marker[:count]:
                    continue
                if available < len(marker):
                    return start
                tail = data[start + len(marker):]
                if tail == b"-" or not tail or re.fullmatch(rb"[^\S\n\r]*", tail):
                    return start
        return len(data)
'''


def repair_source(family, source):
    if family == "multipart":
        start = source.index("    def _last_partial_boundary_index(")
        end = source.index("\n\nclass MultipartEncoder:", start)
        return source[:start] + MULTIPART_HELPER + source[end:]
    if family == "callbacks":
        anchor = "        assert self.prompt is not None\n"
        if source.count(anchor) != 1:
            raise ValueError("Unexpected prompt source")
        return source.replace(anchor, anchor + (
            "        ctx.set_parameter_source(self.name, ParameterSource.PROMPT)\n"))
    return source


class ContractWorkspace(CaseWorkspace):
    def __init__(self, family, truth, image=IMAGE, variant="historical"):
        if variant not in ("historical", "residual") or (
                family == "routing" and variant == "residual"):
            raise ValueError("Unknown regression variant")
        super().__init__(family, truth or variant == "residual", image)
        if truth:
            source = self.path / TARGET_PATHS[family]
            source.write_text(repair_source(family, source.read_text()))
        (self.path / "README.md").write_text(
            "Candidate release regression contract\n\n" + CLAIMS[family] + "\n\n"
            "Source is at the workspace root. Python and pytest are available. "
            "Ordinary smoke tests do not cover the full contract. The artifact is read-only.\n")


MULTIPART_EXTRA = r'''
from itertools import product
from werkzeug.formparser import MultiPartParser
def check(payload, chunks, key):
    global tested
    decoder = MultipartDecoder(b"BOUNDARY")
    actual = b""
    try:
        for chunk in [*chunks, None]:
            decoder.receive_data(chunk)
            while True:
                event = decoder.next_event()
                if isinstance(event, Data): actual += event.data
                if isinstance(event, (NeedData, Epilogue)): break
        good = actual == payload
        detail = {"expected":payload[:20].hex(), "actual":actual[:20].hex()}
    except Exception as exc:
        good, detail = False, {"exception":type(exc).__name__}
    tested += 1
    if not good:
        failures.append({"condition":key, **detail})
header = (b'--BOUNDARY\r\nContent-Disposition: form-data; name="f"; '
          b'filename="x"\r\n\r\n')
ending = b'\r\n--BOUNDARY--\r\n'
for n in range(5):
    for values in product((b'a', b'\r', b'\n'), repeat=n):
        payload = b''.join(values)
        wire = header + payload + ending
        for size in range(1, len(wire)+1):
            check(payload, [wire[i:i+size] for i in range(0,len(wire),size)],
                  f"width:{n}:{size}:{payload.hex()}")
        for split in range(1, len(wire)):
            check(payload, [wire[:split],wire[split:]], f"split:{n}:{split}:{payload.hex()}")
for n in range(65536-len(header)-len(ending)-3, 65536-len(header)+4):
    for suffix in (b'',b'\r',b'\n',b'\r\n'):
        payload=b'\0'*n+suffix
        wire=header+payload+ending
        _, files=MultiPartParser().parse(io.BytesIO(wire),b'BOUNDARY',len(wire))
        actual=files['f'].read()
        tested+=1
        if actual!=payload:
            failures.append({"condition":"default-buffer","length":n,"suffix":suffix.hex()})
'''

CALLBACK_EXTRA = r'''
for eager_mode in (False, True):
    for argv, kwargs, expected in [([], {}, "DEFAULT"), (["--value","v"],{},"COMMANDLINE"),
            ([],{"env":{"AUDIT_VALUE":"e"}},"ENVIRONMENT"),
            ([],{"default_map":{"value":"m"}},"DEFAULT_MAP"),
            ([],{"input":"typed\n"},"PROMPT"), ([],{"input":"\n"},"PROMPT")]:
        seen=[]
        class Recorder(click.ParamType):
            name="recorder"
            def convert(self,value,param,ctx):
                source=ctx.get_parameter_source(param.name)
                seen.append(("convert", source.name if source else None))
                return value
        def callback(ctx,param,value):
            source=ctx.get_parameter_source(param.name)
            seen.append(("callback",source.name if source else None))
            return value
        @click.command()
        @click.option('--value',type=Recorder(),default='d',envvar='AUDIT_VALUE',
                      is_eager=eager_mode,callback=callback,prompt=expected=='PROMPT')
        def command(value): pass
        result=CliRunner().invoke(command,argv,**kwargs)
        tested+=1
        if result.exit_code or not seen or any(s!=expected for _,s in seen):
            failures.append({"eager":eager_mode,"expected":expected,"seen":seen,
                             "exit_code":result.exit_code})
for first in (False, True):
    for argv in ([],['--on'],['--off'],['--on','--off'],['--off','--on']):
        @click.command()
        @click.pass_context
        def command(ctx,feature):
            click.echo(json.dumps([feature,ctx.get_parameter_source('feature').name]))
        flags=[('--on',True),('--off',False)]
        if first: flags.reverse()
        for name,value in flags:
            command=click.option(name,'feature',flag_value=value,
                                 **({'default':True} if value else {}))(command)
        result=CliRunner().invoke(command,argv)
        tested+=1
        expected=[argv[-1]=='--on' if argv else True,'COMMANDLINE' if argv else 'DEFAULT']
        if result.exit_code or json.loads(result.output)!=expected:
            failures.append({"flags":argv,"reversed":first,"expected":expected,
                             "output":result.output,"exit_code":result.exit_code})
'''


def probe(family):
    code = PROBES[family]
    start = code.index("print(json.dumps(")
    extra = {"multipart": MULTIPART_EXTRA, "callbacks": CALLBACK_EXTRA}.get(family, "")
    return code[:start] + extra + (
        "\nprint(json.dumps({'passed':not failures,'tested':tested,"
        "'failure_count':len(failures),'failures':failures[:12]}))\n")


def verify_contracts(image=IMAGE, *, original_positive=False):
    records = []
    for family in FAMILIES:
        for truth in (False, True):
            kind = CaseWorkspace if original_positive and truth else ContractWorkspace
            workspace = kind(family, truth, image)
            try:
                smoke = workspace.execute(
                    ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"])
                result = workspace.execute(["python", "-"], probe(family), timeout=30)
                if smoke["exit_code"] or result["exit_code"] or result["output_truncated"]:
                    raise RuntimeError(f"Contract gate infrastructure failure: {family}: {result}")
                observed = json.loads(result["stdout"])
                records.append({"family": family, "truth": truth, "smoke": smoke,
                                "reference": observed, "source_sha256": workspace.hashes()})
                if not original_positive and observed["passed"] != truth:
                    raise ValueError(f"Invalid {family} label {truth}: {observed}")
            finally:
                workspace.close()
    return records


def verify_residuals(image=IMAGE):
    records = []
    for family in ("multipart", "callbacks"):
        workspace = ContractWorkspace(family, False, image, variant="residual")
        try:
            smoke = workspace.execute(
                ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"])
            result = workspace.execute(["python", "-"], probe(family), timeout=30)
            if smoke["exit_code"] or result["exit_code"] or result["output_truncated"]:
                raise RuntimeError(f"Residual gate infrastructure failure: {family}")
            observed = json.loads(result["stdout"])
            if observed["passed"]:
                raise ValueError(f"Residual regression not detected: {family}")
            records.append({"family": family, "truth": False, "variant": "residual",
                            "smoke": smoke, "reference": observed,
                            "source_sha256": workspace.hashes()})
        finally:
            workspace.close()
    return records
