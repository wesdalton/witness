# Research position, checked 24 October 2026

The user explicitly requested an iterative research loop toward interesting,
validated, novel findings. Novelty is not established by a new name or a null
result on a new fixture. This is a working position, not a priority claim.

## Primary-source comparisons

* [Epistemic Sybil Resistance](https://arxiv.org/html/2609.01873):
  already studies report multiplicity, shared evidence roots, correlated
  extraction errors, and provenance-aware aggregation, including LLM experiments.
  We cannot claim that counting speakers rather than evidence is a new discovery.
* [When Stale Constraints Go Unchecked](https://arxiv.org/html/2608.25553):
  already uses a six-item setting with two verification slots, tests verification
  allocation and budget sweeps, and compares forced and target-blind allocation
  rules. Merely adding a binding budget or a provenance link is not enough.
* [Lie Rarely, Lie Big](https://arxiv.org/html/2610.04744):
  grounded robot-team reports can be re-measured at an opportunity cost, with
  adversarial effects depending on verification rates. Grounded costly checking
  alone is established territory.
* [When Debate Helps](https://arxiv.org/html/2610.04686v1):
  holds proposals fixed while varying evidential peer content and measures its
  effects on answer selection. Controlled peer evidence is not itself new.
* [CONSENSAGENT](https://aclanthology.org/2025.findings-acl.1141/):
  studies sycophancy and prompt interventions in multi-agent debate. General
  claims about harmful conformity are already covered.
* [TestAgent](https://arxiv.org/html/2607.09101): planner/generator/reviewer agents
  use repository tools and feedback to construct tests. Its reviewer-removal
  ablation changes test quality, including mutation score. Thus an agent message
  changing test quality is already demonstrated at the system-component level.
* [MuMuTestUp](https://arxiv.org/html/2605.19265): mutation, coverage, and retrieval
  agents guide test updates. Its mutation-agent ablation lowers mutation score
  while increasing structural coverage, demonstrating that the two measures can
  diverge. Using mutation scores or having agents write tests is not itself new.
  Full methods and ablation sections of both papers were inspected. Our candidate
  distinction is randomizing unsupported endorsement while holding substantive
  evidence and access fixed, then replaying the resulting audit programs. This
  is an inference about these comparisons, not an exhaustive priority claim.

A ClaimArena-LLM search result also overlaps propagation, provenance, and scheduled
verification. Its publisher returned HTTP 429 when opened. No alternate access was
attempted; full-text comparison remains incomplete.

Further targeted review found [Don't Judge Code by Its Cover](https://aclanthology.org/2026.findings-eacl.70/),
which tests authority and other superficial cues in code judgments, including a
condition supplied with generated tests. The appendix's evaluation prompt asks
the judge to simulate or reason about test execution; its test-generation prompt
contains the problem description without the biased code. Thus this is close
prior work on judgments despite test prompting, but the inspected method does not
randomize endorsement before autonomous live probe construction and then replay
those probes. A live tool-use claim alone is still insufficient for novelty.

[CoBiT](https://aclanthology.org/2026.emnlp-main.44/) separately measures confirmation
bias in evidence re-ranking and answer generation for scientific claims. Its
abstract reinforces that separating evidence selection from final judgment is
established practice; full methods comparison remains outstanding.

The next full-text request for CoBiT returned an access error; it was not retried
through another route. Additional primary-source method review found closer work:

* [Audit Without Verification](https://arxiv.org/html/2609.07680) holds reports'
  observations fixed while removing an upstream conclusion field. Its auditor
  attribution changes substantially, with correct-suggestion costs and incorrect-
  suggestion benefits studied separately and replicated across auditors/domains.
  Therefore fixed-evidence conclusion contamination and its trade-off are already
  established; merely moving that manipulation into SQL is insufficient novelty.
  Its inspected auditor outcome is an origin attribution, whereas our candidate
  outcome is a newly constructed executable verification program and its behavior
  on fresh data. That distinction still needs an informative finding.
* [Auditing and Decomposing Feedback-Driven Evolution](https://arxiv.org/html/2608.19626)
  audits single-reference test oracles using independent implementations and
  compares iterative feedback with equal-budget resampling and matched placebo
  feedback. It already separates execution success from semantic validity and
  interaction structure from useful feedback. Our repaired benchmark and fresh
  program replay are validity safeguards, not by themselves research novelty.
* [Contextual Bias in Security Code Review](https://arxiv.org/html/2603.18740)
  includes real autonomous review pipelines. The current v4 differs materially
  from the older abstract surfaced in search; use its current full text. Simple
  framing can fail or backfire, while adaptive metadata refinement is stronger.
  Do not equate a simple endorsement null with robustness to all social context,
  and do not tune stimuli until they manufacture a failure. Our study does not
  deploy vulnerability reintroduction or optimize a code-review attack.

These comparisons narrow the candidate contribution to a measured change in
verification-program semantics, conditional on truthful execution evidence and
fixed access. A claim about causal mediation would require an additional controlled
intervention on the verification procedure; trace correlations alone do not prove it.

## Candidate contribution and falsification

Test whether peer endorsement changes *the evidence-generating procedure* an
auditor constructs: which cases it probes and which actual regression variants
those programs distinguish. Separate this from merely changing final answers or
whether the tool was invoked.

The candidate causal chain is randomized peer context -> investigation allocation
and/or probe construction -> measured fault coverage -> final calibrated decisions.
Replay agent-written probes against paired candidate variants to measure their
discriminating power. A read of a correct source predicate still counts as
verification; an execution that prints results can provide evidence without an
assertion. Different stdout alone is not automatically a valid fault detection.

Two distinct experiments are needed:

1. Allocation: randomize peers before the auditor chooses candidates under a
   binding budget. Estimate target selection and portfolio outcomes.
2. Depth: after an identical, already-opened target and identical initial evidence,
   randomize peer context before new probe construction. This avoids interpreting
   conditioning on treatment-dependent selection as a causal depth effect.

If endorsements improve coverage or leave it unchanged, report that outcome.
If only final beliefs change while evidence acquisition does not, reject the
proposed acquisition explanation. If more tool calls simply repeat the same
non-discriminating test, report redundant work separately. A coverage disclosure
intervention needs a factual-information-matched control; otherwise it may merely
give a debugging hint.

## What would count as validated

Freeze the primary endpoint, effect size worth detecting, sample size, exclusions,
and stopping rule before a confirmatory batch. Use separate development and
replication seeds and at least one genuinely held-out regression family. Repeated
labels and positions from the same few code variants do not create independent
tasks. Obtain paired uncertainty estimates and examine family-level heterogeneity.
Until then, label results calibration or exploratory; never call lack of
significance evidence of equivalence. Priority and external validity require a
broader literature/task check even if a within-environment effect is decisive.

## Concurrency transfer considered after the route ceiling

[CIR+CVN](https://arxiv.org/html/2604.09318) already combines LLM-produced concurrency
artifacts with deterministic validation and bounded exhaustive exploration, including
repair and goal-preservation checks. Its trust boundary is the generated artifact.
[DRPBench](https://proceedings.mlr.press/v306/guo26z.html) evaluates fine-grained race
prediction on 1,003 SV-COMP programs, including reasoning and agentic variants.
[Jain and Purandare](https://arxiv.org/html/2501.14326) study concurrent-program
comprehension and correctness across memory models. Therefore neither difficult
concurrent reasoning nor using exact model checking is itself novel. A prospective
finite schedule task would provide unscaffolded verifier construction for a later
controlled evidence-quality study, not a new concurrency benchmark claim.
These comparisons currently cover CIR+CVN and Jain/Purandare full text and the
DRPBench proceedings abstract; do not overstate full-method review of the latter.

## Closer evidence-quality and recovery comparisons

[Validation Evidence in LLM Repair Agents](https://arxiv.org/html/2607.28871)
already captures validation events at exact code states, separates test-only
changes, and replays them on buggy, candidate and gold implementations. Its
controlled intervention compares replay feedback with both baseline and an
attention-matched reminder, with scaffold/model replications. We inspected the
method and design. Therefore replaying spontaneous probes, separating execution
from discriminating evidence, and adding replay feedback are not novel contributions
for Witness. The remaining unsupported-endorsement manipulation needs an actual
semantic effect and stronger transfer, rather than a renamed replay metric.

[Coding before testing](https://arxiv.org/html/2607.05139) studies dependent code/test
generation and mutually consistent failures; [the ICSE paper](https://conf.researchr.org/details/icse-2026/icse-2026-research-track/15/Measuring-the-Influence-of-Incorrect-Code-on-Test-Generation)
is another direct comparison on incorrect code context. The former full text and
the latter conference record were retrieved; full methods of the latter are not
yet reviewed. Do not claim merely inheriting a faulty implementation biases test
generation as new. [To Run or Not to Run](https://arxiv.org/html/2606.26978) also
compares execution-access policies and their costs in actual repair agents.
Our one-query ceiling and work measurements are narrower diagnostic evidence.

[EpiSEM-Bench](https://arxiv.org/html/2610.31650), published 22 October, pairs
permitted/prohibited worlds, persistently suppresses selected facts while keeping
remaining observations true, and tests active recovery from an independent source.
The paired-world and recovery methods were inspected. Truthful-but-insufficient
evidence plus a recovery tool is therefore already a studied intervention.
[AgentProp-Bench](https://arxiv.org/html/2604.16706) explicitly perturbs schema-valid
tool parameters and separates rejection, recovery and fabricated execution.
Its current v2 methods differ from older search summaries; use the current paper.

[EnvTrustBench's project page](https://envtrustbench.github.io/EnvTrustBench/)
describes failures from stale/incorrect derived state and executable artifacts.
It withholds the manuscript and raw traces, so detailed comparison is limited.
This still defeats a broad claim that auditing a misleading cache or helper
artifact is a wholly new problem. No blocked publisher request was rerouted.

Research decision: no large replication of the present ceilings and no generic
cache-corruption or replay-feedback study purchased on a novelty assumption.
The next proposed contribution must state its distinct estimand, nearest existing
experiment, outcome that would falsify it, and a cheap capability/validity gate.

## Repeatability controls, 28 October 2026

New free work tests repeated execution of the 76 archived Python probes. Ordinary
object representations can contain runtime addresses, so raw stdout differences
need not indicate different behavior. This is a local measurement issue, not a
novel property of agents: [Verifying Determinism in Sequential Programs](https://homes.cs.washington.edu/~mernst/pubs/determinism-icse2021.pdf)
explicitly discusses default object formatting and memory addresses. Its paper was
opened; the comparison does not depend on a secondary summary.

[On the Flakiness of LLM-Generated Tests](https://arxiv.org/abs/2601.08998)
studies repeated tests on four database systems and transfer of flakiness through
prompt context. Only its abstract was reviewed here. Our observation concerns
logged bytes; it must not be described as a changed pass/fail verdict or a new
test-flakiness mechanism. The known BSG-VA and oracle-quality overlaps remain.

A search also surfaced an October preprint about test repair destroying
bug-revealing tests. Its SSRN page returned HTTP 403; access was not retried or
rerouted, and no full-method claim is based on that inaccessible paper.
