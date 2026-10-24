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
