# Live allocation screen: inconclusive, with useful measurement findings

All 32 planned audits were attempted. Four authored endorsements did not produce
a clear reduction in target investigation relative to four neutral receipts.
The uncertainty remains too large to rule out a practically meaningful effect.
This exploratory result is neither equivalence nor a novel behavioral finding.

## Design and outcome

Six-claim portfolios contained five software candidates and one visible arithmetic
control. Agents could open only two candidate workspaces, with revisits free in
investigation credits. The 16 seeds matched candidate source, truth, ordering,
target, and instructions across peer conditions. GPT-6 Luna requested medium
reasoning through Responses, with navigation hints. Peer statements were controlled
authored stimuli, not independent live peer executions.

| Analysis | Matched pairs | Neutral target checks | Endorsement target checks | Difference | Conservative 95% interval |
|---|---:|---:|---:|---:|---:|
| Frozen complete-pair implementation | 13 | 6/13 | 7/13 | +0.0769 | [-0.4554, +0.5631] |
| Post hoc observable-allocation sensitivity | 16 | 8/16 | 8/16 | 0 | [-0.4610, +0.4610] |

The exact paired sign p-value is 1 in both analyses. In the full observable set,
three pairs changed in each direction and ten tied. Intervals combine exact
binomial intervals for the discordant cells with Bonferroni coverage. The
prespecified meaningful allocation change was 0.20; neither analysis excludes it.
The target set contains six multipart, six callback, and four routing cases;
nine targets are true and seven false. These are variations of a small fixed
source corpus, not sixteen independent repositories.

There were 29 completed final submissions. All three incomplete submissions were
in the endorsement arm: a local conservative context limit, an extra unsupported
tool field, and an attempted third investigation. Missingness may depend on
treatment; complete-case effects require that qualification. All three episodes
had already spent their two investigation credits, so their actual allocation
was observable without imputing a final answer. Its sensitivity analysis was
added transparently after the first infrastructure review.

## Validity and implementation changes

The context guard stopped a request before dispatch; its previous successful
request used 24,304 input tokens against a 156,372 byte-based conservative bound.
After review, unattempted episodes continued under a 256,000 bound, still below
the higher-price context threshold. The final continuation allowed an invalid
model action to end its own episode without stopping unrelated planned episodes.
Model-facing prompts, tools, candidates, and validators remained unchanged.
The original manifests and failed traces remain intact, linked through a manifest
hash chain. No episode was retried, repaired, replaced, or silently dropped.

Among completed episodes, 57/58 inspected software verdicts were correct. The
remaining auditor ran 2,465 passing payload checks but incorrectly interpreted
the runtime contract as requiring a shipped exhaustive test suite. This was not
a runtime counterexample. Five submitted probabilities contradicted their verbal
verdicts: four neutral and one endorsement. Preserve literal probabilities; do
not invert them after seeing outcomes.

The descriptive mean paired Brier difference was -0.02278 (endorsement minus
neutral), but probability-direction and interpretation errors prevent a simple
belief-change explanation. Executable probe replays retain their raw outputs;
different output or a nonzero exit alone does not establish useful fault coverage.
Source-only verification is legitimate and unmeasured by inline-program replay.
See allocation-validity-review.md for the individual cases.

## Cost and next decision

This screen used 253 requests, $0.145384115 reported charges, and $2.384928750
retained reservations. Across the whole authorized phase through this stage:
373 requests, $0.389267985 reported charges, and $5.571674625 retained reservations.
The $25 ceiling and append-only ledger are unchanged. The audit found no ledger,
trace, or frozen-source errors. Two historical warnings remain: an early pilot
had hashes without a full source snapshot, and the original invalid v1 scores
remain excluded. No Daybreak rejection occurred in this research loop.

Do not scale this allocation contrast merely to obtain significance. Existing
literature already covers budgeted verification; this screen does not supply a
clear new mechanism. The next small calibration instead separates an executable
verification artifact from its reported belief on an independently validated
finite-data task. It must pass capability and difficulty review before a larger
comparison. See query-protocol-v1.md and loop-decisions.md.

Reproduce the analysis:

```bash
.venv/bin/python scripts/analyze_portfolio_pairs.py \
  research/portfolio/luna-v2-allocation-screen-01 \
  --continuation \
  research/portfolio/luna-v2-allocation-screen-01-continuation \
  research/portfolio/luna-v2-allocation-screen-01-continuation-02 \
  research/portfolio/luna-v2-allocation-screen-01-continuation-03
.venv/bin/python scripts/audit_agent_study.py
```
