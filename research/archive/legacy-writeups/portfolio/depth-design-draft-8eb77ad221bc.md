# Probe-depth experiment — development draft, no dispatch authorized by this file

The allocation study measures which claims receive access. A separate experiment
is required to identify how endorsement changes verification *after access*.
Comparing only selected targets in the allocation study would condition on a
treatment-dependent variable. Treat such comparisons as descriptive.

## Candidate design

Provide one already-opened candidate, an identical claim, smoke report, and initial
source excerpt. The initial excerpt and live smoke result must be generated before
the peer condition is assigned and must match exactly within a pair. Randomize
four neutral receipts versus four endorsements at this point. The auditor can
inspect more source and execute its own probes before submitting a verdict and
probability that the claim is true. Explicitly define the probability direction.
Keep command and response allowances equal across conditions.

Software endpoint: semantically reviewed fault discrimination of the generated
probe collection when replayed unchanged against repaired and faulty versions.
Count independent candidate versions, not number of subtests or tool invocations.
Source-only assessments remain legitimate but unmeasured by executable replay;
report their frequency and evidence separately. Do not code them as zero coverage.
If missing executable probes differ by treatment, report bounds or an explicitly
defined composite endpoint; do not compare complete cases as if randomly selected.

Possible domain transfer: a finite SQLite reconciliation task. Have the auditor
submit its final executable aggregate query alongside its assessment. Replay that
query, unmodified, on fresh databases with independently agreed Python and SQL
reference answers. This measures a program's behavior, not a judge's impression
that a tool call looked useful. Mandatory query submission changes the estimand:
it concerns quality conditional on a required artifact, not voluntary checking.
Keep this distinction explicit rather than pooling domains.

## Gates before spending

1. Finish and review the fixed allocation screen. Decide what uncertainty the
   depth experiment can resolve that further allocation replications cannot.
2. Freeze probe acceptance, semantic grading, missingness, and the primary
   endpoint. Different output alone is not a detected fault. A valid counterexample
   must violate the stated contract; incorrect API use is not one.
3. Validate replay with known good and inadequate programs locally. Ensure an
   assertion-free but informative program is not incorrectly scored as useless.
4. Calibrate any new task/configuration before the comparison. If the task yields
   universal success/failure, revise it for measurement value, not for an intended
   direction of endorsement effect. Record all development attempts.
5. Fix fresh samples, minimum meaningful effect, maximum reservation, analysis,
   and stop rules. Run no paid batch directly from this draft.

## Alternatives to preserve

Endorsement may help prioritize, reduce redundant effort without reducing coverage,
change only reported beliefs, or have no detectable effect. A null result with a
wide interval does not distinguish these possibilities. Four authored endorsements
are a controlled social signal, not evidence of an independently running swarm.

The finite-inventory task and this draft were prepared during the allocation run;
no current effect estimate was used to select their difficulty or peer wording.
