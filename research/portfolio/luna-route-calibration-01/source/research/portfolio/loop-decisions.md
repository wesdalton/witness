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

## Loop 3 result and Loop 4 decision — assess economical replication feasibility

The scarce Sol calibration completed with exactly two opened cases, both correctly
assessed, and three untouched software cases assigned probability 0.5/uncertain.
The arithmetic control was correct without inspection. Brier 0.1250168333 is
close to the ideal 0.125 for perfect checking of two cases and honest uncertainty
on three. Seven responses, eleven commands, $0.0611538. One command failed because
rg was unavailable; the agent recovered with grep. No reference problem arose.

This shows that the budget can bind while permitting effective verification.
It is one portfolio, not a generalized performance claim. Local replay of seven
full-calibration inline programs also shows they can distinguish the known fault
variants; the simplest default-buffer example misses the residual multipart fault.
Different stdout remains a candidate observation until its content is reviewed.

Improvements before more spending: provide package-root/tool availability hints
to every condition in the next configuration. Raise Luna's conservative input
bound to 160,000 within its independently checked short-context pricing contract,
avoiding a predictable 60,000-bound failure on legitimate multi-step audits.
Neither change conveys candidate truth. Prior Sol runs remain separate.

Next paid question: can the economical model conduct useful live investigations
under this two-case budget, making a replicated comparison affordable? Two no-peer
v2 portfolios, seeds 1002 and 1003, navigation hints enabled, GPT-6 Luna with
reasoning disabled and 3072 maximum output tokens. Batch reservation ceiling
$0.35. Inspect all selected-case evidence and uncertainty before a comparison.
Stop on incomplete episodes, accounting errors, or new reference inconsistencies.
If verification capability is inadequate, revise the model/design rather than
calling that peer-induced harm. Do not automatically launch a treatment matrix.

## Loop 4 result and Loop 5 decision — reasoning-enabled economical calibration

The two Luna/no-reasoning episodes completed for $0.001475835 but did not meet the
capability gate. One confused a Werkzeug routing workspace with Click; another
spent a credit recalculating the already-visible arithmetic and left all software
claims uncertain. One source-based negative verdict was plausible but lacked a
concrete counterexample. Therefore no peer matrix on this configuration.

Competing explanation: the economical model's configuration, with reasoning
disabled, encourages premature termination. Before paying for a large Sol
comparison, run the same two no-peer seeds with Luna requesting medium reasoning
through Responses and 4096 output tokens, retaining navigation hints and all case
contracts. This changes API/output capacity as well as reasoning; it is a
configuration-capability check, not an isolated causal estimate of reasoning.
Maximum reservation $0.50. Stop on incomplete runs or any validity/accounting
failure. If selected software claims remain mostly unverified, do not tune peer
wording to elicit a treatment effect; use the already capable model or redesign.

## Loop 5 result and Loop 6 decision — fixed exploratory allocation comparison

Reasoning-enabled Luna completed both portfolios with useful verification of all
four selected software candidates, correct arithmetic without spending a credit,
and probability 0.5 on the three uninspected software candidates in each portfolio.
Reviewed live counterexamples cover multipart byte loss and routing misassignment;
callback evidence includes all five sources and destination arbitration. Costs:
17 responses, $0.00918167, $0.174114125 retained reservations. The provider reports
nonzero reasoning tokens in this configuration. This clears the capability gate.
It is a configuration comparison, not proof that reasoning alone caused the gain.

Phase total after these gates: 120 requests, $0.243883870 reported charges,
$3.186745875 retained reservations. We can now afford a replicated exploratory
contrast without using a model that failed the underlying task.

Paid question: do four endorsements change which target candidate receives one
of two live investigations, compared with four neutral receipts? Freeze 16 pairs,
seeds 2001 through 2016, neutral and endorsement arms, v2/navigation hints,
Luna/medium/Responses, 4096 output tokens, otherwise unchanged. Maximum retained
batch reservation $5. The statistical plan is in screening-01.md. This batch
finishes its planned sample regardless of interim effect direction; stop only on
validity, incomplete-episode, API/accounting, or Daybreak problems. No automatic
retry or fallback. Review failures before resuming in a new documented batch.

Expected information: estimate the direction and size of allocation response,
detect ceiling/floor behavior, and assess whether any difference warrants
independent confirmation or whether the next test should isolate probe depth.
Probe replay and final beliefs are secondary diagnostics. No novel or conclusive
claim follows from this adaptively designed pilot alone.

## Loop 6 infrastructure result and continuation decision

The batch stopped at its own byte-based context ceiling after eleven complete
audits and one incomplete audit; twenty planned specs were never dispatched.
No Daybreak/provider rejection occurred, and the ledger/source/trace audit has
no errors. The original data support only three complete pairs, far too few for
an allocation conclusion. Preserve the probability/verdict contradiction observed
in one completed answer rather than flipping its score.

Repair the infrastructure contract before spending again: retain full native
history and conservative byte reservations, but explicitly review a 256,000
Luna/Responses ceiling below long-context pricing. Offline tests confirm oversized
requests still stop before reservation, the higher bound charges the full payload,
and other models cannot use the expansion. A continuation selector excludes every
already-started spec, including the failed one.

Freeze screening-01-continuation.md; run only the twenty unattempted specs in their
original order, with the same prompts/tools/candidates/settings. Maximum retained
reservation $12 (reviewed worst case $10.89536) inside the original phase ceiling.
Do not retry episode 012 or add seeds. This repairs a pre-dispatch infrastructure
limit and completes the selected sample; it is not effect-driven sample extension.
Stop on any incomplete or unreconciled stage again, review, and preserve evidence.

The continuation then completed six episodes before one invalid tool call with
an extra unsupported field. This is a model action-format failure; keep it as such.
Do not fix the answer or relax schema validation. Continue only the thirteen
untouched original specs under the same settings, with a $7.1 maximum reservation
and a manifest chain recording the review. See the continuation protocol addendum.

A later episode attempted a third case after exhausting its credits. The validator
correctly rejected the bundle. Keep that model failure too. Finish the ten still
untouched specs with a $5.5 maximum reservation and an explicitly frozen operational
change: invalid_action still ends its own episode, but does not stop unrelated
planned episodes. All infrastructure/accounting/Daybreak stops remain mandatory.
No model-facing behavior, validation, episode retry, or sample extension changes.

## Loop 6 completed result and Loop 7 decision

All 32 originally planned episodes were attempted: 29 complete, one local-context
infrastructure stop, and two invalid model actions. All three incomplete final
submissions were in the endorsement arm; complete-case comparisons must acknowledge
that asymmetry. No failed episode was repaired, retried, or replaced. No Daybreak
rejection occurred. The final ledger/trace/source audit has no errors.

The frozen complete-pair analysis has 13 pairs: target selection differs by +0.0769
(endorsement minus neutral), conservative 95% interval [-0.4554, +0.5631], exact
paired sign p=1. The separately labeled observable-allocation sensitivity uses all
16 pairs: both arms investigated 8/16 targets; three pairs changed each way and ten
tied. Difference 0, interval [-0.4610, +0.4610], p=1. This is inconclusive about the
predefined 0.20 meaningful effect, not evidence of equivalence. The small fixed
source corpus also limits external validity.

Do not buy a large allocation replication now: the screen supplies no clear
direction, prior work already covers budgeted allocation, and interpretation of
the secondary Brier difference is compromised by reversed probability fields and
a claim-interpretation error. The more informative next step is to measure the
generated verification artifact separately from the answer on an exact finite task.

Authorize within the existing phase ceiling the four-episode no-peer query
capability calibration frozen in query-protocol-v1.md: seeds 8001 and 8002, both
truth states, Luna/medium/Responses with strict tool schemas. Maximum reservation
$1.1. Phase before dispatch: 373 requests, $0.389267985 reported cost,
$5.571674625 retained reservations. The free reference, mutation, isolation,
replay, and no-leakage gates pass. Review every query and all unseen-world replays.
If it is a one-query ceiling, decline a larger peer sweep on this task. If it
fails capability, revise before treatment testing. No automatic comparison or
novelty claim follows from this calibration.

## Loop 7 result and free Loop 8 development

All four query audits and their final programs were correct on the observed data
and all sixteen fresh replay worlds each. Two used one query and two used three,
but every first aggregate query was correct; extra calls inspected schema/category
counts. No format or probability-direction inconsistency appeared. Twelve requests
cost $0.003185340 with $0.044003750 retained reservations. This is capability
validation, not evidence that the new task is intrinsically difficult.

Decline a bare-report peer sweep on this likely ceiling. Develop a sharper
inherited-program challenge: provide an actual, plausible SQL program and its
truthful execution receipt, with correct and subtly incorrect implementations.
Neutral and endorsement conditions must receive identical substantive evidence.
Measure whether the auditor constructs a correct final verification program
on fresh data rather than merely replaying the inherited mistake. Keep authored
programs/peer stimuli distinct from independently executing peer agents.

## Loop 8 paid capability decision

The eight live inherited-program reference checks passed, with unchanged databases
within each seed and truthful published execution results. All 135 local tests
pass. The free checks establish finite labels and isolation; only real auditor
calls can establish whether a supplied plausible program changes task difficulty.
Freeze query-inherited-protocol-v1.md and run eight no-peer episodes, seeds
11001–11004 in both program-truth states, one fault family per seed. Maximum retained
batch reservation $2.2, inside the existing phase ceiling. Replay final programs
unchanged on sixteen fresh worlds each and review every trace before another
paid decision. No automatic peer matrix, retries, or result-dependent replacement.
Phase before dispatch: 385 requests, $0.392453325 charges, $5.615678375 reservations.

## Loop 8 result and free Loop 9 development

All eight inherited inventory audits completed correctly. Each first aggregate
query was correct, and all final programs passed sixteen fresh database conditions.
No interpretation or probability-direction inconsistency was found. Twenty-one
requests added $0.006220050 charges and $0.079480625 retained reservations.
Phase totals: 406 requests, $0.398673375 charges, $5.695159000 reservations.
Do not buy a larger social comparison on a task that remains straightforward.

Develop a new joint optimization task with independently checked finite labels:
minimum combined cost of two routes with internal-node and risk-group disjointness.
The natural greedy publisher program is compared with a correct program on identical
graphs; both supply truthful execution receipts. Free checks include exhaustive
five-node graphs under three risk assignments, semantic mutations, renamed nodes,
infeasible graphs, and repeated risk groups within one route. A paid capability
decision requires those gates and a frozen protocol first. This is a new task;
do not pool it with inventory or describe seeded graphs as independent real projects.

## Loop 9 paid capability decision

The first free replay gate missed the greedy fault; preserve that failed gate.
After adding reference-qualified fresh greedy traps before model inference, all
nine authored mutations have counterexamples. All 30 live replay conditions and
eight planned supplied-program labels pass. The exhaustive small-graph comparison,
138 local tests, and ledger/source/trace audit pass. Freeze route-protocol-v1.md.
Run eight no-peer route audits, seeds 14001–14004 in both publisher-program states,
maximum reservation $2.2 within the unchanged phase ceiling. This spends on an
algorithmic capability question that free reference checks cannot answer; it
does not assume the task will be hard or authorize a subsequent peer matrix.
