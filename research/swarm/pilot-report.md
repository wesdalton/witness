# Initial real-model pilot — 18 October 2026

In the completed true/false pair, all eight agents eventually requested the probe
and ended on the correct answer. No agent was classified as mistaken at a recorded
round end. This small setup did not produce the hypothesized harmful cascade.

This is an exploratory infrastructure pilot. It does not identify the proposed
effect of agreement on verification, establish a treatment advantage, or calibrate
the 10,000-node browser simulation. The raw successful and unsuccessful runs are
included in the source archive, alongside the batch manifests. Every episode records
the harness and prompt hashes. The batch manifests for the first two batches
(`luna-calibration-01`, `luna-pilot-seed42`) predate the pilot-runner source hash;
the later four record it.

## Design and observed outcomes

Requested model: `openrouter/openai/gpt-6-luna`, pinned to the `openai` provider,
reasoning disabled, maximum 256 output tokens, provider sampling defaults. All runs
use report-only context and a two-round delay before returning a recorded probe.
The matched pair uses eight agents, eight synchronous rounds, seed 42, and 24 effort
units per agent. A check costs four; sending a message costs one. Receiving evidence
costs no action units. The two ledger fixtures share an identical passing-test report;
their hidden ground truth and recorded probe results differ.

| Episode | Agents × rounds | Invalid responses | Agents checked | Checks / delivered / pending | Final correct / uncertain / wrong | Mean wrong | Effort used |
|---|---:|---:|---:|---:|---:|---:|---:|
| False report calibration | 4 × 4 | 0/16 | 4/4 | 6 / 4 / 2 | 100% / 0% / 0% | 0.0% | 29 |
| True report | 8 × 8 | 7/64 | 8/8 | 10 / 10 / 0 | 100% / 0% / 0% | 0.0% | 78 |
| False report | 8 × 8 | 0/64 | 8/8 | 11 / 11 / 0 | 100% / 0% / 0% | 0.0% | 88 |

Mean wrong covers rounds 1–T. The four-agent calibration has a different horizon and
is shown separately; it is not another matched replicate. No forced checks were used.
Every check retrieves the same fixed `probe:0` observation. Six requests, for example,
do not imply six independent observations. The calibration ended with two checks
still pending.

All eight agents in the true-report episode eventually requested a check and ended
on the correct answer. Seven responses contained extra text after the JSON object;
the parser rejected them and retained the prior belief while executing abstention.
They remain in the denominator. The harness does not record termination reasons,
so this pilot cannot generally distinguish malformed output from truncation.

## Operational failures and accounting

Two unpaced expanded attempts stopped after 20 valid requests and a provider error.
The second recorded HTTP 429, with one attempt and no automatic retry. A separate
restart dispatched zero requests because the budget guard incorrectly treated a
request ID from another batch as a duplicate. That bug was fixed and regression-tested.
All three episodes are retained and excluded from behavioral comparisons.

The fresh true-report run used a 3.2-second minimum request interval and completed
all 64 responses without a provider error. Its malformed responses stopped the
automatic matrix at the episode boundary. After inspecting those format errors,
the false fixture was collected in a separate batch with the same prompt, model
settings, pacing, population and horizon. No output was silently repaired or retried.
The six-condition treatment matrix remains incomplete.

The audit records **186 dispatched requests** across all attempts.
OpenRouter reported **US$0.0110639** used on the dedicated key at
2026-10-18T15:30:21.982393+00:00. Conservative retained reservations total **US$1.2718080**;
reservations are not charges. Locally blocked slots after a failure are neither
model responses nor additional paid requests.

## Interpretation limits and next experiment

- This is one model, one seed, and one ledger case family. Agents within an episode
  are dependent. No significance test or general model ranking is warranted.
- The setup gives every agent access to a definitive probe. One check and seven
  relays cost 11 of the available 24 effort units; that policy faces no binding
  budget tradeoff here. Agreement is not randomized. These runs cannot establish
  communication crowding out checking.
- The planned reserved arm combines ancestry visibility and forced first-round
  checking. Compare it against the ancestry arm to isolate compulsory checking;
  forced checks must not be counted as voluntary choices.
- Ancestry follows declared citations. Authentic receipt IDs do not guarantee that
  a relay faithfully summarizes them, and omitted citations lose ancestry.
- Matching seeds matches networks and initial exposures, not API sampling or token
  expenditure. Agents see the current round but not the episode's ending round;
  late pending checks are therefore not evidence of knowingly wasted effort.

Before broadening the study, record termination reasons, evaluate structured-output
support, and make the decision horizon explicit. Treat changes as a new configuration,
with new hashes. Then run the protocol's frozen-state experiment: vary endorsement
count and shared-source visibility while holding the evidence and available budget
fixed. Include true reports, false reports, and no-peer controls across distinct cases.
That experiment can test the acquisition hypothesis; the current pilot cannot.

## Harness changes after this pilot (v0.2)

These changes follow review of the pilot. They alter future episodes, so v0.2 runs
must not be pooled with the episodes above.

- Graph construction and report seeding now use independent random streams. In v0.1
  both read one stream, so on small-world graphs every agent that received the
  report also received an extra shortcut link. Same-seed v0.2 networks differ from
  the recorded ones; each manifest stores its graph, seeded agents and `rng_scheme`.
- A positive report share always seeds at least one agent. With four agents, about
  29% of seeds previously gave the report to nobody. `seed_share=0` remains a
  deliberate no-report control.
- Each decision records the provider's stop reason. An opt-in `--parse-mode lenient`
  accepts a leading JSON object and flags `format_violation`; strict remains the
  default. Strict-mode rejections record whether lenient parsing would have recovered
  them. All seven rejected outputs above were a valid decision followed by degenerate
  trailing text, which is itself a model-behavior observation worth keeping.
- In the reserved arm, the model view now states that the first-round check is
  executed regardless of its chosen action.

## Inspect and reproduce

- Public machine-readable [episode summary](pilot-summary.json) and [cost/error audit](pilot-audit.json).
- [Download the complete source and raw pilot records](https://witness-evaluation-lab.beigeglade34.chatgpt.site/assets/witness-source.zip).
- Canonical source paths: `research/swarm/pilot-summary.json`, `pilot-audit.json`,
  `pilot-plan.md`, and the six pilot directories listed in the audit.
- Recompute an episode summary: `python -m swarm_lab.analyze RUN.json --out SUMMARY.json`.
- The original pre-pilot plan and later operational amendments are preserved in
  `research/swarm/pilot-plan.md`; the broader scientific design is in `protocol.md`.

Live calls are stochastic and billable; rerunning the analysis of saved records is
local and free. The website runs the authored mechanistic engine, not these LLMs.
