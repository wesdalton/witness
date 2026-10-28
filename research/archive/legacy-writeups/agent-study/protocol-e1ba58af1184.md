# Live verification study — protocol v0.3

Prepared 24 October 2026, before the new live calls. This is a development pilot,
not an external preregistration or a confirmatory study. The October 18 decision
pilot remains separate: its checks retrieved recorded observations.

## Decision and research question

Build a single autonomous auditor before building a communicating swarm. The
auditor can inspect source and execute its own Python in an isolated container.
Ask whether supplied peer endorsements change acquisition of evidence beyond a
passing test report. First establish that tool use and measurement work.

The narrow claim is that the supplied ledger includes the end date in both
`balance(as_of=...)` and `statement(start, end)`. Ground truth is executable and
held outside the agent's workspace. The existing honest correction and pytest
module-substitution fixture form one paired case family, not two independent tasks.
The initial report is identical across the pair. No fixture name, truth label,
host path, or reference answer is included in the agent's initial observation.

## Agent and tools

A fresh model context receives the claim, a report, the available effort and turn
limits, and any assigned peer context. It chooses native function calls to list
files, read files, run the supplied tests, execute arbitrary Python, or submit an
assessment. Tool results come from the actual workspace, not a recorded probe.
Python executes with no network, no host credentials, read-only case files, an
unprivileged user, and process, memory, time, and output limits. Scratch space is
temporary. Each execution gets a fresh container; persistence between executions
is deliberately absent. The auditor assesses the submitted artifact, not a repair.

Listing or reading costs one effort unit; a test run or Python execution costs
four; submission is free. The initial budget is eight. There are at most eight
model responses, with a forced submission opportunity on the last response.
These action units are experimental constraints, not monetary costs or measured
human effort. No instruction requires verification or assumes peers are wrong.
Multiple independent tool calls may be requested in one model response. Each
action is charged separately; the complete bundle is validated against the
remaining effort before any action executes. Submission must be requested alone.

## Stage gates and spending

The user authorized **at most US$25 across this phase**, including pilot and
follow-up requests. A persistent ledger reserves a conservative maximum before
every request. It retains reservations after failures and rejects resets,
overruns, and unknown charges. Provider routing is pinned, retries disabled,
and current token prices checked against the model catalog before dispatch.
The dedicated provider key also has a non-resetting cap. Do not interpret this
ceiling as a spending target. Existing October 18 reservations are not reset.

1. **Free validity gate:** test label isolation, action accounting, submission
   validation, spend ceilings, timeouts, and reference outcomes. Demonstrate
   that a fresh Python execution distinguishes both fixtures while the reported
   outcome does not. Do not buy model calls before this passes.
2. **Calibration:** two fresh episodes per truth value, no peers. Use an economical
   model first. Review every transcript. Stop on provider/billing errors. Stop the
   batch on malformed tool calls or output truncation rather than silently
   repairing and pooling. An agent failing to submit remains an observed failure.
3. **Screening, conditional on calibration:** no peers, four neutral peer messages,
   four endorsements, and the same endorsements with explicit shared ancestry.
   Initially use two repetitions per truth value per arm (16 episodes). Randomize
   order using a recorded seed, not an alleged deterministic API seed. Review
   after this batch; no automatic expansion.
4. **Replication, conditional on screening:** a second model or new case family
   must resolve a specific uncertainty exposed by earlier stages. Document the
   reason, expected information, and worst-case spend before dispatch.

At every gate assess: whether results answer the intended question; measurement
errors; floor/ceiling effects; unnecessary context/tool cost; competing
explanations; and the cheapest next observation that would change a decision.
Record changes and reasons before further calls. Never tune a fixture just to
produce the desired failure, merge changed configurations, or conceal null runs.

## Manipulations and estimands

Peer messages are **authored experimental stimuli**, not outputs of independently
running peers. This isolates exposure to endorsements in a live-tool auditor;
it is not an experiment on emergent multi-agent communication. Neutral messages
control approximately for number, role labels, and text length. Exact tokenizer
length and wording are not matched, so endorsement effects remain specific to
this stimulus. No-peer comparisons additionally change context length.

All endorsements derive from the same initial report. The ancestry arm discloses
that common root and the absence of independent checking. It estimates the effect
of that disclosure, including its instructional salience. It does not identify
a pure ancestry data-structure effect.

Primary descriptive endpoint: any attempted live evidence acquisition before
submission, and first action. Separately report source reads, supplied-test
execution, agent-written Python execution, successful processes, effort spent,
verdict, confidence, Brier score, completion, and infrastructure failures.
**A Python call is not automatically an independent or adequate verification.**
Review code and outputs manually at pilot scale; record whether it actually
tests the claimed behavior, merely repeats a report, or does something else.
Source inspection can also establish this simple claim without executing code.

Every attempted episode stays in the audit. Provider failures, malformed outputs,
truncation, and no submission are separate categories, not wrong answers or
silent exclusions. Report the denominator for every metric. Repeated calls and
agents within one case family are not independent task replications. No population
claim, significance claim, or calibrated swarm dynamics follows from this pilot.

## Go / no-go decisions

If tool use or transcript completeness fails, fix infrastructure before expanding.
If both paired conditions are solved reliably with source inspection, that is a
valid outcome: do not call the absence of execution a verification failure.
If acquisition is at a ceiling in every arm, stop buying repetitions of this
configuration. Consider realistic opportunity costs or a different case family,
preserving and reporting the easy-task null result. If errors appear, check the
reference and read the evidence before attributing them to social influence.

## Prior work and scope

Sources checked 24 October 2026. Abstract-level checks constrain claims; this is
not yet an exhaustive literature review.

- [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657)
  provides a taxonomy of system failures, including verification/termination.
  Witness needs measured interventions, not another taxonomy.
- [Agreement Overstates Evidence](https://arxiv.org/abs/2609.22512) studies
  correlated judge errors. Agreement and independent evidence are already known
  to differ; the question here is whether exposure changes evidence acquisition.
- [LLMs Trust Their Own](https://arxiv.org/abs/2609.33495) studies identity-dependent
  conformity. Hold peer identity labels fixed; do not describe an ordinary
  conformity effect as a new finding.

Native tools and model settings were checked against
[OpenRouter tool calling](https://openrouter.ai/docs/guides/features/tool-calling),
[reasoning accounting](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens),
and [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).
Provider catalog snapshots and per-call usage accompany the run records.

## Amendment after first calibration attempt

The first batch stopped on its second response: after listing files, the model
requested three source/specification reads in one response. The initial harness
incorrectly treated this normal native-tool behavior as an invalid call count.
Two calls cost US$0.0001471; no assessment was submitted. Retain this attempt as
an infrastructure failure, not a behavioral outcome. Before further calls, v0.2
allows independent tool bundles with per-action accounting and atomic budget
validation. Source/prompt/protocol hashes distinguish the configurations.

## Amendment after the 16-episode ledger screen

Every screened episode acquired source evidence and reached the correct verdict.
Stop repetitions of that configuration: it has an acquisition ceiling. The lack
of a reward for unused effort also means there is no meaningful opportunity cost
to verification. This does not establish that peer agreement is harmless generally.

Before a larger study, add one data-dependent family: audit a monthly total against
an actual SQLite transaction database. The same report claims 43,210 cents in both
fixtures. Correct and incorrect variants differ only in whether a 900-cent row is
inside the inclusive date interval, giving independent reference totals of 43,210
and 42,310. Other accounts, negative adjustments, and out-of-period transactions
must be handled correctly. Specifications and file inventories are identical.

This is an authored matched pair. The aggregate report is a stipulated claim, not
an LLM-generated publisher report or a historical production incident. The agent
can inspect schema/specification and must obtain row data to substantiate the
aggregate; it may write its own SQL/Python. The agent does not receive reference
code, expected results, truth labels, or fixture names. Text reads identify binary
files without rendering their bytes. Live Python has ordinary SQLite access.

First buy only four no-peer calibration episodes to test agent-written execution,
with the existing model/settings and $0.50 batch ceiling. This new configuration
is separate from the ledger screen. Review the exact queries and denominators
before any further comparison. Its purpose is capability and measurement, not
creating an error or salvaging the original hypothesis.
