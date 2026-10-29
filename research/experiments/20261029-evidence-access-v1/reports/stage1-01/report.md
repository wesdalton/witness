# Stage 1 calibration: auditors commit on evidence that cannot decide the claim

29 October 2026. Pilot on the 32 development incidents; not a test of H1 or H2.
320 episodes, 0 invalid outputs, $0.264 billed. Every response reconciles with the
phase ledger. Raw runs: [Luna](../../runs/stage1-luna-02/),
[Sol](../../runs/stage1-sol-01/). Numbers: [analysis](../../analyses/stage1-01/analysis.json).

## What we found

**Neither model abstains on a test-run report alone.** Within every pair, the
report is byte-identical for the valid and invalid run, so the only correct answer
is `insufficient`.

| Report-only claims | GPT-6 Luna | GPT-6.1 Sol |
| --- | ---: | ---: |
| "Patch passes the hidden suite" (12 incidents) | 12/12 committed | 12/12 committed |
| "Passes within the time limit" (8) | 8/8 committed | 8/8 committed |
| "5/5 attempts passed" (12) | 12/12 committed | 7/12 committed |
| Invalid claims accepted | 16/16 | 15/16 |

Every committed report-only verdict was `supported`. Sol's only abstentions were
on the attempt-rate claim.

**With full access, both models resolve almost everything.** Luna answered 30/32
exactly and Sol 31/32. Sol's one miss refuted a valid claim by ignoring the
declared exclusion of an infrastructure failure.

**Partial access shows where the errors are (Luna, 8 access sets).**

- When the only extra evidence was the manifest, which cannot separate runner
  substitution, Luna accepted all 8 invalid runner-substitution claims. It read
  "exit 0, passed" as confirmation.
- When the replay alone was given, which does separate these pairs, Luna still
  accepted all 4 early-exit runs, citing "the replay exited successfully". The
  replay showed exit code 0 and no test summary. It refuted all 4 shadow-runner
  runs, whose replay showed real failures. **The auditor repeated the publisher
  harness's own mistake: trusting exit status 0.**
- When the artifacts alone were given, Luna accepted 3 of 4 invalid
  time-limit claims despite truncated logs with no summary line.

**H1's direction was not observed.** In 48 paired comparisons, adding a
non-separating channel never turned an abstention into a commitment. In 16
pairs it did the reverse: Luna committed on the report but answered
`insufficient` once given the irrelevant channel.

## Decision

Do not run Stage 2 as frozen. H1 asks whether non-separating evidence *raises*
commitment, but report-only commitment is already 100% (Luna) and 84% (Sol).
That leaves no room to rise, which violates the calibration rule in AGENTS.md
(baseline roughly 30% to 70%). The frozen sample-size rule gives 236 pairs. That
would be money spent on a contrast these data show cannot be detected.

Two observations are worth confirming on held-out tasks under a new frozen
protocol (v2):

1. **Commitment under proven insufficiency, by claim type.** Single-run claims
   drew no abstentions from either model. This is the cleanest candidate result.
   The prior work to compare against is the literature on calibrated abstention.
2. **Inherited failure modes.** An auditor given the verifier output still trusts
   exit status 0 when the summary is missing (4/4 early-exit runs). The sample
   is small: 4 incidents, one model, one sample each.

Before v2: author the four further held-out tasks the protocol requires, then
size v2 from these Stage 1 rates.

## Limitations

- Development tasks only, one sample per cell, one provider.
- Sol saw only two access sets.
- Luna produced a mean of 234 reasoning tokens with medium reasoning requested.
- The first Luna launch aborted before dispatch on a path error; it is sealed as
  `stage1-luna-01`.
