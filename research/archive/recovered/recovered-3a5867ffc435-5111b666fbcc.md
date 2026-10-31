# Witness findings

Current report for every Witness study, as of 29 October 2026. Raw runs stay at
their original paths. The detailed historical writeups are sealed, unchanged,
under [`archive/`](archive/) and linked below.

## Summary

- **First confirmed behavioral result (31 October, held-out tasks, two models):**
  LLM auditors accept a test report that provably cannot decide the claim, and
  they treat a verifier's exit status 0 as proof even when no tests are shown to
  have run. Scope: authored fixtures, one provider.
- Two results hold up, and both are about measurement validity:
  1. A capable auditor exposed two wrong reference labels in our own benchmark.
  2. Agent-written probes can print different text on identical code because of
     memory addresses. Raw output differences are therefore not fault detection.
- Every capability task built between 24 and 28 October hit a ceiling: every
  completed audit was correct.
- The one treatment comparison, the allocation screen, could not have produced an
  answer as designed (see [Why the earlier studies found nothing](#why-the-earlier-studies-found-nothing)).
- The active question is now the evidence-access benchmark
  ([directions.md](directions.md), Option 1); see the next section. AGENTS.md has
  the design rules.

## Active study: evidence-access benchmark

Frozen [protocol](experiments/20261029-evidence-access-v1/design/protocol.md),
29 October 2026. The question: when the evidence an auditor holds provably
cannot separate a valid run from an invalid one, does it abstain or commit? And
does adding a channel that cannot separate the pair raise false acceptance?

The corpus is 48 incidents from real container runs. There are six small
libraries (four for development, two held out) and three failure families:

- runner substitution
- dropped attempts
- timeout reported as success

The publisher's report is byte-identical within every pair. Each family can only
be separated by different channels:

| Family | Artifacts | Manifest | Replay |
| --- | --- | --- | --- |
| runner_substitution | separates | no | separates |
| dropped_attempts | no | separates | no |
| timeout_as_success | separates | separates | separates |

All free gates passed with zero model calls
([gates](experiments/20261029-evidence-access-v1/gates/corpus-v1/gates.json)).
Two independent references confirm every label. The report never separates a
pair, and no label words appear in the visible channels. An identifiability-aware
deterministic checker is exact under all eight access sets. A naive checker that
never abstains falsely accepts 25% to 50% of invalid claims when given a
non-separating channel. That is the behavior H1 asks about in LLM auditors.

**Stage 1 calibration** (pilot, 320 episodes, $0.264;
[report](experiments/20261029-evidence-access-v1/reports/stage1-01/report.md)):

- **Report only.** Given only the report, where the correct answer is always
  `insufficient`, GPT-6 Luna committed on 32/32 incidents and GPT-6.1 Sol on
  27/32. Every commitment was `supported`. They accepted 16/16 and 15/16 invalid
  claims. Neither model ever abstained on a single-run claim.
- **Full access.** Both models resolved nearly everything: 30/32 and 31/32.
- **Inherited mistake.** Given the verifier's output, Luna still accepted all 4
  early-exit runs because the exit code was 0, though no test summary appeared.
  That is the same mistake the publisher's harness makes.
- **H1 not observed.** Adding a non-separating channel never raised commitment;
  in 16 of 48 pairs it lowered it.

With report-only commitment at 84% to 100%, H1 has no room to show an increase,
so Stage 2 did not run as frozen. v2 below replaced it.

**v2 held-out confirmation** (frozen protocol, 2,112 episodes, $2.685;
[report](experiments/20261031-evidence-access-v2/reports/stage2-01/report.md)).
This ran on 64 incidents from 8 tasks never used for design. Primary tests use
Bonferroni-corrected cluster-bootstrap intervals.

- **P1 confirmed for both models.** With only the byte-identical report, Luna
  committed on 191/192 and Sol on 172/192. They accepted 96/96 and 85/96 invalid
  claims.
- **P3 confirmed for both models.** Given only the verifier record of an
  early-exit run (exit code 0, no test summary), both accepted 48/48. Both refuted
  48/48 runs whose replay showed failures. Sol often noted the missing summary
  and accepted anyway.
- **P2.** Confirmed for Sol: it committed on 120/120 single-run claims and 52/72
  attempt-rate claims. Not for Luna, as predicted.
- **Telling the auditor the rule** cut report-only commitment to 0/192 for both
  models. It cut exit-status acceptance only for Luna (48 to 14 of 48); Sol stayed
  at 43/48.
- **A benchmark label defect surfaced.** Valid attempt-rate claims are not
  actually established, because no per-attempt patch binding exists. It affects
  only a secondary guard; see the
  [adjudication](experiments/20261031-evidence-access-v2/adjudications/dropped-attempts-labels-01/adjudication.md).

The closest prior work, [Trusting the Tool](https://arxiv.org/abs/2610.32876),
found similar deference to unverified analyzer output. These results come from
authored fixtures and two models from one provider. Testing model families from
other providers is next.

## Spending

The current phase ledger is [`agent-study/budget.jsonl`](agent-study/budget.jsonl)
($25 ceiling). The 18 October pilot has its own ledger and is not included in
these phase totals.

| Study | Requests | Billed |
| --- | ---: | ---: |
| 18 Oct swarm pilot (separate ledger) | 186 | $0.0110639 |
| Single-claim auditor (4 batches) | 78 | $0.009717865 |
| Portfolio calibrations (Sol v1, Sol v2 ×2, Luna ×2) | 42 | $0.234166005 |
| Allocation screen (4 continuation batches) | 253 | $0.145384115 |
| Query capability series (6 batches) | 217 | $0.060714225 |
| Evidence-access Stage 1 (Luna 256, Sol 64) | 320 | $0.264261165 |
| Evidence-access v2 (Luna 1,056, Sol 1,056) | 2,112 | $2.685563065 |
| **Phase total** | **3,022** | **$3.399806440** |

Rows are summed from the ledger by batch. Phase exposure equals billed cost
because every request settled.

## Studies

### 1. Swarm pilot, 18 October: recorded-observation agents

Eight GPT-6 Luna agents passed messages for eight rounds about a true or a false
ledger report. Every agent eventually requested the single fixed probe and ended
correct, so no harmful cascade appeared. The probe was a recorded observation and
the budget never forced a trade-off. This is an infrastructure pilot. The 10,000-
agent browser model is an authored simulation that these runs do not calibrate.
Current report: [swarm/pilot-report.md](swarm/pilot-report.md).

### 2. Single-claim auditor, 24 October: live tools

One auditor checked one ledger claim using live file reads and Python in a
container. Calibration and a 16-episode, four-arm peer screen were all correct
(16/16), and four SQLite calibration episodes wrote correct queries. The task was
at ceiling, so the peer arms could not differ.
Archived: [decisions](archive/legacy-writeups/agent-study/decisions-d42687e3f23b.md),
[report](archive/legacy-writeups/agent-study/report-0fee8a063b32.md),
[next-experiment draft](archive/legacy-writeups/agent-study/next-experiment-701447918250.md).

### 3. Portfolio v1 calibration: two wrong benchmark labels

GPT-6.1 Sol audited six claims built from real Werkzeug and Click regressions.
It refuted two claims we had labeled true, with executable counterexamples that
reproduced in fresh containers: multipart parsing appends a CR with a one-byte
buffer, and a prompted eager option sees source `None`. Our finite reference tests
had not covered those conditions. V1 accuracy and Brier scores are excluded
everywhere. The counterexamples are local contract violations, not established
upstream bugs.
Archived: [report](archive/legacy-writeups/portfolio/report-6e11aecd6a10.md),
[upstream position](archive/legacy-writeups/portfolio/upstream-counterexample-position-96292849743b.md),
[decisions](archive/legacy-writeups/portfolio/decisions-0a28bde42a9e.md).
Raw: [sol-calibration-full-01](portfolio/sol-calibration-full-01/),
[adjudication](portfolio/sol-calibration-full-01/adjudication.json).

### 4. Portfolio v2 and the allocation screen

Repaired v2 labels passed an expanded gate. With six credits, Sol verified all six
claims correctly; with two, it checked two and left the rest at 0.5. Luna with
reasoning disabled failed the capability gate. Luna with medium reasoning passed.

The screen then ran 16 matched pairs: four neutral receipts versus four
endorsements on a target claim, with two investigation credits.

| Analysis | Pairs | Neutral | Endorsement | Difference | 95% interval |
| --- | ---: | ---: | ---: | ---: | --- |
| Frozen complete pairs | 13 | 6/13 | 7/13 | +0.08 | [-0.46, +0.56] |
| All observable allocations | 16 | 8/16 | 8/16 | 0 | [-0.46, +0.46] |

Result: inconclusive, not equivalence. All three incomplete episodes were in the
endorsement arm. Five submitted probabilities contradicted their own verdicts.
Frozen plans: [protocol-v2](portfolio/protocol-v2.md), [screening-01](portfolio/screening-01.md),
[continuation](portfolio/screening-01-continuation.md).
Archived: [screen report](archive/legacy-writeups/portfolio/allocation-screen-report-b78aeecfbe63.md),
[validity review](archive/legacy-writeups/portfolio/allocation-validity-review-85f307a9d2ad.md),
[loop decisions](archive/legacy-writeups/portfolio/loop-decisions-c6b9c47661da.md),
[loop report](archive/legacy-writeups/portfolio/loop-report-beebd9a0cbe0.md).

### 5. Query capability series: six ceilings

Each task gave a finite claim plus a truthful execution receipt, and the auditor
queried a SQLite database. Every completed audit was correct. Every requested
program also passed its fresh replay worlds.

| Task | Episodes | Correct | Archived report |
| --- | ---: | ---: | --- |
| Inventory query | 4 | 4 | [query calibration](archive/legacy-writeups/portfolio/query-calibration-report-e9314eaeff73.md) |
| Inherited near-correct SQL | 8 | 8 | [inherited query](archive/legacy-writeups/portfolio/inherited-query-calibration-report-a1676bb35686.md) |
| Disjoint routes | 8 | 8 | [routes](archive/legacy-writeups/portfolio/route-calibration-report-027293e0dfd5.md) |
| Output requirement × peers | 32 | 32 | [output requirement](archive/legacy-writeups/portfolio/output-requirement-report-c97d254ddb71.md) |
| One-query budget | 8 | 8 | [scarce query](archive/legacy-writeups/portfolio/scarce-query-report-099a8d5c4b0d.md) |
| Concurrent schedules | 4 | 4 | [schedules](archive/legacy-writeups/portfolio/schedule-report-c75fa87687a1.md) |

A follow-up measured work inside single queries. Replacing recursive `UNION ALL`
with `UNION` cut SQLite progress units 40 to 52 times with identical answers. That
is a SQL optimization, not a research result.
Archived: [query work](archive/legacy-writeups/portfolio/query-work-report-49463967853d.md).

### 6. Probe replay repeatability, 28 October

All 76 archived Python probes were replayed twice against each implementation:
223 pairs and 446 executions, with no API calls. Two probes printed object memory
addresses that changed between identical runs. One of them produced two archived
"differences" that disappear once the address is removed. Prospective
replay now repeats each execution and flags address-only differences. This
improves measurement; it is not a finding about agents.
Report: [edition 01](experiments/20261028-probe-repeatability-v1/reports/edition-01/report.md).

### 7. Three-library repository audit: stopped before setup

An automated command guard rejected the setup command on 28 October. Under the
user's standing instruction, it was not retried. No corpus was built.
Record: [repository-audit-status-20261028.md](repository-audit-status-20261028.md).

## Why the earlier studies found nothing

An external audit on 29 October 2026 found four design problems. The provenance
was sound.

1. **Weak treatment.** The endorsement was four identical copies of "I reviewed the
   smoke report. My assessment is that this claim is supported." The system prompt
   had already called smoke reports insufficient and told the model it was an
   independent auditor.
2. **Underpowered.** With 6 of 16 pairs discordant, detecting the frozen 0.20
   effect at 80% power needs about 72 matched pairs (McNemar approximation). The
   screen had 16 pairs, at roughly $0.005 per episode.
3. **Ceilings.** Tasks were never calibrated to an intermediate baseline before a
   comparison, so no treatment could move the outcome.
4. **Confounds and accounting.** Duplicate claim texts left about three effective
   bug families. The screen had no no-peer arm. The ledger counted 14 times the
   billed spend against the cap ($6.43 vs $0.45); settlement fixed this on
   29 October.

[Novelty review](archive/legacy-writeups/portfolio/novelty-review-bd45737c36e0.md)
(24 October) shows that peer endorsement and budgeted verification are already
well studied. The evidence-access benchmark is the less crowded direction.

## Limitations

- Models: GPT-6 Luna and GPT-6.1 Sol through OpenRouter only.
- Corpus: three regression families from two projects (Werkzeug, Click), plus
  authored SQLite tasks. Repeated seeds are not independent repositories.
- Peer messages were authored stimuli, never independently executing agents.
- Finite reference checks do not prove universal correctness. One v1 contract
  also allowed integer overflow; its finite labels remain valid
  ([adjudication](portfolio/route-numeric-adjudication.json)).
- The earliest calibration batch has hashes but no full source snapshot.

## Other archived material

[Artifact requirement hypothesis](archive/legacy-writeups/portfolio/artifact-requirement-hypothesis-3834461bb08f.md),
[depth design draft](archive/legacy-writeups/portfolio/depth-design-draft-8eb77ad221bc.md),
[held-out development](archive/legacy-writeups/portfolio/heldout-development-013d0c88da45.md),
[identical-evidence baseline](archive/legacy-writeups/portfolio/identical-evidence-baseline-4be0a4a8548c.md),
[route development](archive/legacy-writeups/portfolio/route-development-59c45704f19f.md),
[next-loop options](archive/legacy-writeups/portfolio/next-loop-options-79223165eaa1.md),
[archive completeness, 28 October](archive/recovered/recovered-0d08359ae4be-a4ae80f8e294.md).
The full index of sealed bundles is [registry/index.md](registry/index.md).
