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
