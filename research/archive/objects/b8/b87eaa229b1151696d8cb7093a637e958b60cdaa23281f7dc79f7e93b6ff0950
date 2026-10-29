# Executable query audit: capability calibration protocol

Prepared before any inference on this task. Dispatch requires the preceding
allocation screen's review and a recorded decision in loop-decisions.md.
This is a new task/configuration, not a pooled extension of the portfolio sample.

## Task and measurement

One inventory database is already available. The model receives its complete
reconciliation contract, schema, disputed publisher total, and a truthful database
integrity report. It can execute read-only SQL, then submits a verbal verdict,
probability that the publisher's claim is true, and an executable aggregate query.
Query quality is assessed separately from its belief. The probability direction
is explicit: p_support means probability of a true claim, not verdict confidence.

Generator revision 2 includes status and movement revisions, as-of cutoffs,
half-open effective dates, posted/void movements, cancellations, signed returns,
warehouse filtering, out-of-order arrival, and missing order status. It is an
authored finite-data task, not a historical upstream bug. Independent Python and
SQL implementations must agree on every generated answer. Both generator
revisions and failed development checks remain available.

The database, report, contract, and schema are read-only. The model sees no
reference query, expected total, truth label, generator seed, or generation code.
Live query results are observations from its own program. Final artifact grading
is never fed back to the model. The evaluator does not repair generated SQL.

Replay each submitted query unchanged on seeds 9001–9008, both truth states,
with the same contract and parameter values. Exact signed integer equality is
required. Malformed, truncated, non-scalar, floating-point, boolean, and failed
results have no valid aggregate; they are not imputed as zero. These sixteen
test worlds are conditions for one program, not sixteen independent model trials.
The model is told its submitted query will be tested on additional databases.

## Initial calibration

Four no-peer episodes: seeds 8001 and 8002, each in true and false report states.
The report is identical within each true/false world pair, while a source quantity
changes. Randomize execution order with the runner's fixed stream. GPT-6 Luna,
medium reasoning, Responses, 4096 maximum output tokens, provider defaults for
sampling, at most eight responses and eight live queries per episode.

Prospectively use strict function schemas to prevent unsupported fields, with all
object fields required and additionalProperties=false. This is supported by the
[official function-calling contract](https://developers.openai.com/api/docs/guides/function-calling)
and the [Luna feature list](https://developers.openai.com/api/docs/models/gpt-6-luna).
Retain local semantic/citation/query-budget validation. Strict output does not
guarantee sound SQL, calibrated probabilities, or correct judgments.

Record source/prompt/schema/model/image hashes before the first request. The free
gate checks 64 worlds with both reference implementations; separate local checks
have distinguished 15 incorrect SQL variants and validated isolated query/replay
execution. Docker isolation, no network, read-only mounts, byte/output limits,
SQL authorization, and query execution limits remain active.

Maximum retained batch reservation $1.1; worst case $1.089536 at the reviewed
256,000 input-bound units and 4096 output tokens for 32 requests. Use the existing
$25 phase ledger with all earlier reservations retained. No retry or fallback.
Stop on any incomplete episode, new reference inconsistency, provider/accounting
problem, or Daybreak rejection. Do not use another route after a rejection.

## Decision criteria

Inspect every live query, probability, verdict, and replay result. Four episodes
are a capability/measurement calibration, not a population performance estimate.
Do not automatically dispatch neutral/endorsement arms even though the harness
can represent them. A separate frozen decision is required for that experiment.

If every artifact succeeds with one straightforward query, treat the task as a
likely ceiling and decline a large comparison on it. If verification is mostly
unsuccessful, improve task/model capability before a peer test. Intermediate
behavior may justify further independent calibration or a focused depth hypothesis.
Any difficulty revision must precede treatment testing and be recorded regardless
of whether it produces an interesting effect. Null and beneficial effects remain
valid outcomes; novelty requires an additional substantive result and replication.
