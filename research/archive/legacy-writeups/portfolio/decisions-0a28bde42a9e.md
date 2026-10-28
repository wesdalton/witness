# Portfolio research decision log

## Gate 0 — free validation before the stronger-model calibration

The prior study's source-reading ceiling and lack of competing claims make more
repetitions uninformative. The user additionally requested a hard experiment.
We selected three real regression families spanning two projects and independently
checked source provenance. All six candidate variants pass their ordinary smoke
test. Hidden live probes distinguish the three corrected and three broken variants:
51 multipart, seven callback, and sixteen routing conditions per variant. The
broken variants fail 40, four, and six conditions respectively. No model has seen
those probes. This establishes ground truth, not model difficulty.

Improvement over the design draft: use a capable model first, with access to all
cases, to separate technical verification ability from forced allocation. A weak
model's failure alone would not establish a meaningful challenge. Use five
software claims plus a no-cost arithmetic control, isolated workspaces, proper
probability scoring, and atomic bundle validation to make the budget real.

Paid question: what investigations does GPT-6.1 Sol need, and can it justify the
six verdicts in seed 1001 under unrestricted case access? This determines whether
scarce-budget and peer comparisons can be interpreted. One portfolio, maximum
16 responses, medium reasoning, 4096 output tokens per response, batch reservation
ceiling $4 inside the existing $25 phase. No retries, no fallbacks. Stop on any
invalid/incomplete episode, API/accounting defect, or unresolved reference failure.
Review every executed command and final rationale before another paid batch.

Free prerequisites: passing unit tests and lint, live reference gate, sandbox
isolation, deterministic scoring baselines, and native Responses history tests.
All source and protocol files are frozen by the runner before the first request.

## Gate 1 — calibration invalidates two positive reference labels

`sol-calibration-full-01`: one complete six-claim portfolio, seven responses,
23 shell commands, five software candidates opened, $0.079943 reported cost.
The model correctly answered the arithmetic control without opening it. It wrote
live Python probes for all three software families. Ordinary reads were sometimes
truncated; the agent followed up with smaller ranges and execution.

The raw scorer reports 4/6 correct and Brier 0.3231506667. That score is invalid:
the model produced reproducible counterexamples for both supposed positive cases.
The multipart candidate appends a carriage return under valid small-chunk parsing;
the Click candidate exposes source None during the first conversion/callback of
a prompted eager option. Both broad claims include those inputs. A fresh replay
of each exact agent command matched the original stdout. The original reference
suite omitted these conditions; its successful gate was insufficient.

Decision: stop all further inference, including the planned scarce-budget stage.
Keep raw results unchanged and add explicit adjudication. Exclude invalid-label
accuracy and Brier from the audit summary. Add a live-run guard and a regression
test proving it stops before any run or provider access. Preserve counterexamples
as executable artifacts. The finding justifies paying for a stronger calibration
before a large matrix: it prevented us from attributing oracle errors to agents.

This does not establish that the task defeats a strong model, nor that peer
messages suppress verification. The model justified all six decisions against
the stated claims. There was no peer treatment in this calibration. The corpus
has only three families across two projects and reuses related source variants.

Next free work: revise the broad claims and candidate labeling together; strengthen
the oracle with systematic chunk partitioning and every claimed parameter-source
path. Keep these observed counterexamples in the gate. Prefer explicit behavioral
contracts or documented benchmark repairs over silently narrowing scope to mark
valid agent counterexamples wrong. Freeze a new protocol, independently validate
its positive and negative candidates, then consider one new capability calibration.
Do not simply remove the live guard to resume v1 or buy a peer matrix now.

The user then instructed us to stop actions blocked by Daybreak. No new API runs
were started. Future rejections must be treated as stops, without alternate routes.
