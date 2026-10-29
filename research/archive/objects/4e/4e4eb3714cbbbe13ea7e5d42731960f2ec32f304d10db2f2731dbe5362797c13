# Iterative research log — 24 October 2026

The user explicitly requests a continuing experiment -> review -> hypothesis ->
implementation loop, aiming for interesting, validated, novel findings. Continue
independent authorized work after ordinary findings or failed hypotheses rather
than ending at a proposed next step. Maintain the existing spending ceiling and
the instruction to stop at Daybreak rejections without alternate routes.

## Loop 1, free reference repair

Hypothesis: two missing reference dimensions explain the apparent model errors:
closing-boundary fragmentation and source timing inside prompts.

Implementation: preserve original source bytes and v1 labels; add new benchmark
positives with local repairs and explicit contracts. Expand systematic reference
coverage and replay the original positive versions against it. The original
multipart positive fails 631/21,686 conditions; the original callback positive
fails 4/29. Repaired positives pass all conditions. Historical negatives fail
7,187/21,686 and 16/29 respectively; routing remains 6/16 failures in the negative.

The first free gate attempt exposed a mistake in the *new test*: it explicitly
assigned conflicting defaults to both shared-destination flags while assuming
one fixed winner. Corrected the test configuration to assign the intended default
only once. This was a test-specification error, not another agent or library result.

Conclusion: the expanded gate distinguishes the intended states, including the
agent's counterexamples. Passing this finite gate is not proof against all new
counterexamples. Preserve both residual failures as negative candidate variants.

Literature review: a two-of-six verification setup already exists in stale-memory
research. Revise the candidate contribution toward experimentally identifying
changes in agent-written probe coverage, with allocation and depth tested
separately. See novelty-review.md; novelty remains provisional.

## Loop 2, paid capable-model recalibration

Question: can the same capable model provide valid assessments of repaired
positives and multiple negative variants, without exposing another label error?
This is necessary before interpreting allocation/coverage effects. Cheaper local
checks cannot substitute for an independent agent constructing unanticipated tests.

Freeze v2; run one no-peer seed-1001 portfolio, six credits, GPT-6.1 Sol, medium
reasoning requested, 4096 output tokens, no retries/fallbacks. Maximum retained
reservation for this batch: $3, inside the existing phase limit. Stop on invalid
action, incomplete output, infrastructure/billing uncertainty, or a new credible
counterexample. Review all evidence before the next stage. A new reference
problem triggers another free repair loop, not a peer sweep.

## Loop 2 result and Loop 3 decision — make the allocation constraint bind

The v2 full-access calibration completed: six model responses, 21 shell commands,
all six verdicts justified by arithmetic or relevant source/execution evidence,
Brier 0.0000338333, reported cost $0.0824117. The positive multipart candidate
passed 3,339 agent-written decoder checks plus 1,269 end-to-end checks. Callback
probes covered all five sources and shared destinations. Negative source behavior
matched its counterexamples. No new reference inconsistency appeared on review.
This is capability validation; a successful strong model is not evidence of
intrinsic task difficulty.

Improve measurement before treatment: implement local replay of exact inline
Python probes against repaired, historical, and residual variants. Record
unparsed commands separately and require semantic review of differing outputs.
Source-only reasoning is unmeasured by this replay, not deemed a failure.

Next paid question: with only two investigations, does the same auditor respect
the budget, allocate to useful claims, and remain calibrated on unseen candidates?
Run the same seed 1001, no peers, v2, two credits, otherwise unchanged model and
settings. Maximum batch reservation $2. Review its evidence and uncertainty before
any peer comparison. This one matched-seed comparison diagnoses the constraint;
it does not estimate a population treatment effect. Stop on any incomplete episode,
new credible counterexample, or accounting/infrastructure problem.
