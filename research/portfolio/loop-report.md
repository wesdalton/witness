# Witness research loop — 24 October 2026

Real live-agent experiments have run. There is no validated novel behavioral
finding yet. The fixed allocation screen is complete and inconclusive; the next
stage tests verification quality when a plausible program is already supplied.

## Validated observations

The first capable software auditor found reproducible errors in two candidates
labeled correct. Expanded checks found 631/21,686 multipart failures and 4/29
callback failures in those original positives. Separate local repairs passed
the expanded checks; v1 remains disabled and its original accuracy scores invalid.

Sol and Luna/medium passed the repaired portfolio capability gates. Luna without
reasoning did not. Reasoning, API, and output capacity changed together, so this
is a configuration comparison, not an isolated causal reasoning effect.

The fixed 32-episode allocation screen attempted every planned episode: 29
completed and three incomplete, all three in the endorsement arm. No failed
episode was retried or replaced. Among the 13 complete pairs, target selection
was 6/13 neutral versus 7/13 endorsement, difference +0.077, conservative 95%
interval [-0.455, +0.563]. Actual allocation was observable in all 16 pairs;
the labeled sensitivity analysis gives 8/16 in each arm, difference 0, interval
[-0.461, +0.461]. Neither establishes equivalence or rules out a meaningful effect.
See [the completed report](allocation-screen-report.md).

Trace review found five probability/verdict contradictions and one mistaken
interpretation of a runtime claim. Preserve literal submissions and Brier scores;
do not silently flip probabilities. Selected-case correctness and replay depth
are descriptive, not causal estimates conditional on post-treatment selection.

Four no-peer inventory-query audits then produced correct verdicts and SQL on
their observed databases and all sixteen fresh conditions each. Every first
aggregate query was correct. This likely ceiling does not justify a large
bare-report comparison. See [the calibration report](query-calibration-report.md).

## Current stage

The [inherited-query pilot](query-inherited-protocol-v1.md) adds an actual supplied
SQL program and truthful execution receipt. Four plausible semantic faults and
four correct controls passed free reference checks. Eight no-peer audits are
frozen to measure whether auditors recover correct verification programs.
No inherited-query model inference has run at this report revision.

Agents execute real queries and tools. Peer messages and supplied faulty programs
are authored stimuli, not independently executing peer agents. Fresh database
replays evaluate programs; they are not additional independent model trials.

## Interpretation and spending

Prior work already covers budgeted verification, multiplicity/provenance, and
multi-agent test generation. The candidate question concerns endorsement and the
quality of the evidence-generating program, but novelty remains provisional.
See [the literature comparison](novelty-review.md). A novel causal claim requires
fresh confirmation, stronger transfer, and a full comparison with related work.

Before the inherited-query pilot: 385 requests, $0.392453325 reported cost and
$5.615678375 retained reservations. The append-only phase ledger is authoritative;
the total ceiling remains $25. Reservations are conservative limits, not charges.
No Daybreak rejection has appeared in visible outputs in this loop. Any rejected
action must stop without retrying or using an alternate route.
