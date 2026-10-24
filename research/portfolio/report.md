# Harder live-agent calibration — 24 October 2026

**The stronger agent found two errors in our expected answers.** Both
counterexamples reproduced in fresh containers. Further inference on this
protocol is disabled until its reference labels are repaired.

This is a useful research result: the initial tests would have misclassified
successful adversarial verification as model mistakes. It is not evidence for a
peer-influence effect or proof that this task is hard for strong models.

## What ran

One live GPT-6.1 Sol auditor assessed six competing claims: two multipart upload
candidates, two CLI callback candidates, one routing candidate, and one arithmetic
control. Software cases derive from historical regressions in
[Werkzeug multipart parsing](https://github.com/pallets/werkzeug/pull/3081),
[Click parameter-source timing](https://github.com/pallets/click/pull/3484), and
[Werkzeug routing](https://github.com/pallets/werkzeug/pull/3254).
These are three families across two projects, not a diverse benchmark.

The auditor had six case-investigation credits, 24 shell commands, and 16 model
responses. It used seven responses and 23 commands, investigated all five software
candidates, and answered the visible arithmetic without spending an investigation.
No peer messages were supplied. It wrote and executed probes in isolated containers;
the harness supplied neither the probe code nor reference answers.

The initial reference gate passed all six candidate variants: ordinary smoke tests
passed regardless of the assigned label, while 51 multipart, seven callback, and
sixteen routing conditions distinguished the assigned positives and negatives.
Those finite tests did not justify the broad positive claims.

## Counterexamples and adjudication

| Candidate | Original label | Agent evidence | Adjudication |
|---|---|---|---|
| C4, multipart | Supported | With a one-byte buffer, payload `abc\n` becomes `abc\n\r`. An end-to-end parser probe reproduces the discrepancy. | The broad byte-preservation claim is false. |
| C3, callbacks | Supported | A prompted eager option sees source `None` during its initial custom conversion and callback; later processing sees `PROMPT`. | The broad source-availability claim is false. |

The agent also executed 10,832 short payload/chunk combinations on each multipart
candidate. It found 506 mismatches in the supposed positive, and 3,582 in the
known broken candidate. These are correlated probe conditions, not independent
statistical samples. Its routing probe showed misassignment at 11–16 converters;
its callback probe distinguished ordinary source paths before testing prompting.

Fresh replays of the two counterexample commands returned identical stdout:
[replay records](counterexample-replays.json). These are failures of our stated
claims on the recorded versions. We have not established novelty, checked every
current upstream version, or filed an upstream report.

The original artifact retains its mechanical score of 4/6 and Brier loss
0.3231506667. **Do not interpret that as model accuracy:** two reference labels
were wrong. A separate [adjudication](sol-calibration-full-01/adjudication.json)
records the correction, and the audit excludes this batch's accuracy/Brier from
valid-score aggregates. The six submitted decisions have supporting arithmetic
or executable counterexamples under the original claims. This is a post-run
adjudication, not a new independently scored benchmark result.

## Accounting and reproducibility

| Scope | Requests | Reported cost | Retained conservative reservations |
|---|---:|---:|---:|
| This calibration | 7 | $0.079943 | $1.084935 |
| Entire authorized phase | 85 | $0.089660865 | $1.217083625 |

The phase ceiling remains $25. Reservations are not charges and are never reset.
These amounts cover inference only. Response costs reconcile with the append-only
ledger. The earlier provider-key reconciliation covers the prior cycle only; no
new key-balance reconciliation was requested after the user's Daybreak instruction.

The [manifest](sol-calibration-full-01/manifest.json) freezes source, vendor files,
protocol, prompts, model catalog, settings, and image ID. The model route was
`openai/gpt-6.1-sol`, pinned to OpenAI through the Responses endpoint, requesting
medium reasoning and 4096 maximum output tokens, with retries/fallbacks disabled.
The provider reported zero reasoning tokens in these responses; the requested
setting is not evidence that internal reasoning occurred. Public tool traces and
answers are retained. Native private output items, if present, have only metadata
and hashes in public records.

The runner defaults to a dry run. `--live` now stops before creating a new run or
accessing a provider because this protocol has invalid labels. Frozen historical
sources retain the implementation that actually ran. Existing artifacts remain
auditable with `python scripts/audit_agent_study.py`; no inference is needed.

Final local validation: 101 Python tests passed, lint passed, and the artifact
audit found no trace, billing, or frozen-source mismatches. It explicitly warns
about this batch's invalid labels and the earlier pilot's missing full snapshot.

## Next decision

Do free reference repair before more inference: cover chunk partitions and all
claimed parameter sources, preserve the agent's counterexamples, and establish
valid positive candidates under a new explicit contract. Then reassess whether a
small scarce-budget calibration would change a research decision. The present
result does not justify buying a peer-treatment matrix.

The user's Daybreak instruction is an additional operating constraint: stop
blocked actions and do not reroute them. See [stage decisions](decisions.md).
