# Replay differences can be incidental — 28 October 2026

Two historical between-implementation comparisons were flagged as different only
because an agent-written probe printed an object's runtime memory address. Both
flags came from one probe; they are not two independent agent failures. The
original reports already required semantic review and did not treat these flags
as a fault-coverage score. Original outcomes and raw evidence remain unchanged.

## Experiment and result

The frozen exploratory audit included all 76 Python probes in the existing replay
records: 49 multipart, 22 callback and five routing probes. Sixty-six originated
from Luna and ten from Sol sessions. These are correlated probes from the earlier
few-family corpus, not 76 independent tasks. We did not select only suspicious
outputs. Each archived variant was replayed twice in a fresh isolated container,
with source hashes checked against the archived workspace before execution.

| Observation | Result |
| --- | ---: |
| Distinct archived probes | 76 |
| Probe/implementation pairs | 223 |
| Fresh local executions | 446 |
| Pairs with timeout or truncated output | 0 |
| Pairs whose identical-source repeat changed raw text | 5 |
| Probes responsible for those changes | 2 |
| Archived raw between-implementation differences | 118 |
| Differences entirely removed by repr-address normalization | 2 |
| New API requests / charges | 0 / $0 |

The 446 executions belong to this audit. A further 18 local executions validated
the prospective replay implementation on three selected regression-control probes;
these are software validation, not additional independent observations in the table.
The raw results are in [the run](../../runs/repeat-01/completion.json), with exact
inputs in [the frozen selection](../../gates/input-selection/selection.json).

### Case 1: entirely incidental difference

Probe `a76c8aed425b…` prints parser events and `repr(NeedData)`. Its event sequence,
payload and final API-use exception are the same across the three implementations.
Only the address within `<NeedData object at 0x…>` differs. All three same-source
repeat pairs reproduce this nuisance variation. The two archived comparisons
against historical/residual variants become identical after removing just that
address. They provide no evidence that this probe distinguishes a runtime defect.
See [probe 009](../../runs/repeat-01/probe-009.json).

### Case 2: useful differences alongside incidental variation

Probe `c9731e145777…` prints a function object when it finds corrupted payloads.
That repr also varies, but the substantive difference survives: the repaired
implementation prints `all passed`; the historical version loses a CR payload,
and the residual version appends a CR to an empty payload. Source and payload
inspection support those runtime counterexamples. Both broken-variant repeat
pairs vary only in the printed function address. Discarding every probe with
variable text would incorrectly discard useful evidence here.
See [probe 062](../../runs/repeat-01/probe-062.json).

Additional descriptive inspection, outside the primary endpoint: 20 archived
variant executions print a leading `FAIL` while returning exit code zero; one
probe only prints source code. Neither exit status alone nor stable text
differences establish a valid behavioral oracle. These observations do not mean
all such agents reached incorrect final conclusions.

## Implementation and decision

Prospective `witness.probe-replay.v2` records two executions per implementation,
reports identical-source variation, flags address-only differences, and preserves
normalized behavioral differences. It explicitly leaves semantic fault detection
unset pending review. It does not relabel historical records. Unit controls cover
address-only noise, real failure text with noise/zero exit, and pure source dumps.
A fresh replay of the three probes from original episode 004 reproduced the
address-only flags: [validation artifact](../../gates/replay-v2-regression/control.json).

Future paid peer experiments must measure specific bugs using validated test
oracles or reviewed semantic outcomes, include repeated identical-source controls,
and preserve tool/process success separately from test success. Do not infer
additional bugs from raw text inequality. No new paid batch was dispatched.

## Scope, novelty and next hypothesis

This is an exploratory measurement finding in Witness. Two repeats can expose
variation but cannot prove determinism. Memory-address nondeterminism is already
documented in [Verifying Determinism in Sequential Programs](https://homes.cs.washington.edu/~mernst/pubs/determinism-icse2021.pdf).
[BSG-VA](https://arxiv.org/html/2607.28871) already measures validation evidence
across code states. [LLM-test flakiness work](https://arxiv.org/abs/2601.08998)
also studies repeated executions and transfer through context (abstract reviewed
here). Our variable log bytes are not evidence of flaky pass/fail verdicts, a new
general failure mechanism, or a causal effect of peer endorsement.

The next candidate hypothesis remains whether a genuine prior reviewer's
conclusion changes the *additional specific defects found* when its executable
tests and truthful execution results are held fixed. This audit improves the
measurement needed for that test; it does not test the hypothesis itself. The
separately blocked three-library corpus setup remains stopped and is not retried
as part of this audit. Research may continue through independent evidence review
and design work within the existing $25 phase authorization.
