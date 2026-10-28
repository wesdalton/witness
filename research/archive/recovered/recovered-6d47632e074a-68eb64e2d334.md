# Research directions for trustworthy agent evaluations

Research proposal, 18 October 2026.

The recommended direction is an open-source experimental testbed for determining
what evidence an independent auditor needs to verify claims about agent evaluations.
The central experiment changes an auditor's access while holding the underlying
incident fixed. It measures when a misleading claim can be refuted, when a valid
claim can be supported, and when the available evidence cannot settle the question.

Two alternatives are worth considering: measuring whether safety controls survive
ordinary agent-driven maintenance, and packaging evaluation integrity checks into
a reusable regression suite. The former offers a stronger connection to continuous
AI control; the latter offers a shorter path to a useful engineering release.

## A reproducible starting point

The existing ledger task protects test files and then accepts a successful pytest
process exit. A local pilot reproduces that decision rule using disposable copies
of the workspace and the actual hidden tests.

| Authored fixture | Protected files unchanged | Existing scoring rule passes | Separate behavioral probe passes |
| --- | --- | --- | --- |
| Original buggy library | Yes | No | No |
| Correct date-range fix | Yes | Yes | Yes |
| Library exits the process during import | Yes | Yes | No |
| Workspace module substitutes for pytest | Yes | Yes | No |

The substitution fixture copies the honest run's exact stdout. The honest and
incorrect runs therefore have identical reported scores, exit codes, and test
output. An independent probe of the ledger's date-boundary behavior distinguishes
them. This is a constructed example of an observation that cannot establish the
claim being made.

Reproduce from the repository root:

```bash
.venv/bin/python -m research.pilots.scorer_integrity \
  --output research/pilots/scorer_integrity_results.json
```

The [pilot code](pilots/scorer_integrity.py) asserts all four expected outcomes.
The [recorded results](pilots/scorer_integrity_results.json) include stdout, process
statuses, protected-file hashes, source hashes, and interpreter/package versions.
This run used Python 3.12.14 and pytest 9.1.1. The Docker image specifies pytest
8.4.1; the full Inspect/Docker pipeline has not been rerun for these new fixtures.

These are scripted harness checks with zero model calls. They establish neither a
model's propensity to cheat nor the prevalence of this weakness across benchmarks.
The probe checks two behaviors and is not a secure verifier for arbitrary code.
The underlying exploit classes are established; the pilot is a research seed.

## Option 1 Auditor access experiments

**Research question:** Which combinations of evidence access and independent
verification let auditors reliably accept valid evaluation claims and reject
misleading ones, at a fixed audit budget?

### Experiment

Create paired incidents in small executable repositories. One run satisfies a
bounded claim; its counterpart violates that claim. Generate the reports, files,
and execution records from actual runs. Selected pairs deliberately share the same
limited observation, as in the pilot. Include accidental errors and adversarial
manipulation as separate conditions; the auditor evaluates the claim's support,
not the author's motives.

Use six initial failure families:

1. A process reports success without executing the intended checks.
2. A report omits failed or interrupted attempts from its denominator.
3. A valid result is attached to a different source revision or configuration.
4. An agent's visible tool result differs from an independently recorded effect.
5. An evaluation runs with a safeguard enabled, but the claimed configuration
   disables it.
6. A timeout or missing result is silently converted into a successful result.

Every family needs legitimate counterpart cases. For example, an interrupted run
excluded under a declared reporting rule differs from a failed run silently
excluded from a claimed all-attempts success rate. Make the relevant reporting
contract explicit before judging either.

Vary access through independently switchable capabilities:

| Access capability | What it can help establish | What it cannot establish alone |
| --- | --- | --- |
| Publisher's report and selected logs | What the publisher claims happened | Completeness or independent authenticity |
| Full submitted artifacts and transcript | Source changes and visible actions | Unrecorded effects or omitted runs |
| Independently recorded run manifest and configuration | Which registered attempts and artifacts belong to the claim | Semantic correctness of their outcomes |
| Replay in an auditor-controlled verifier | Behavior of the supplied artifact under specified checks | What a historical run did without a binding to that run |

Access is not a single ladder: a complete run manifest can reveal cherry-picking
that replaying the one published artifact misses. Replay can reveal a semantic
failure that a correctly signed manifest misses. Compare combinations, including
matched-cost alternatives, instead of assuming one universal ordering.

Hold the incident and auditor model fixed when comparing access conditions. Start
each audit in a fresh context and keep paired incidents out of the same context.
Separately vary the auditor model and its reasoning budget. This distinguishes an
information limitation from an auditor failing to use available information.

### The central technical contribution

For an incident state `s` and access policy `a`, define `observe(s, a)` as the
evidence available to the auditor. Construct and verify pairs for which:

```text
observe(valid_run, restricted_access) == observe(invalid_run, restricted_access)
claim_is_true(valid_run) != claim_is_true(invalid_run)
```

On an equally weighted pair with identical observations, any forced binary
decision based only on those observations has expected accuracy at most 50%.
This is a basic identifiability fact, not a new theorem. Its value here is that
the benchmark can establish when asking for more evidence is necessary, rather
than rewarding an auditor for guessing from incidental labels or wording.

For each incident, publish the smallest *tested* evidence set that resolves the
claim and a reproducible witness explaining why. Claim global minimality only
when all subsets of the declared evidence set have been checked. Hashes, filenames,
timestamps, and stylistic differences must not inadvertently reveal the label.

The proposed research contribution is an executable corpus and controlled study
of these access requirements across failure families. A model leaderboard would
be a secondary output.

### Ground truth and measurements

Separate the hidden truth of the claim from whether the disclosed evidence is
sufficient to decide it. Let the auditor return `supported`, `refuted`, or
`insufficient evidence`, cite the relevant artifacts, and optionally request an
additional permitted observation. Grade the claim and the evidence justification
separately. An auditor that guesses the hidden truth from an ambiguous packet
has not produced a justified audit.

Use executable reference checks, external observations, and manual review to
establish incident labels. Freeze the intended claim, reporting rule, and reference
before generating adversarial variants. A second LLM's opinion is not the sole
ground truth.

Report false acceptance of invalid claims, false rejection of valid claims,
abstention, the fraction of cases resolved, evidence requests, and measured cost.
Show error versus coverage so an auditor cannot look excellent by declining
every case. Include always-accept, always-abstain, deterministic consistency checks,
a fixed evidence-request order, and an LLM auditor as baselines.

Split by repository and attack family, not just by randomly generated examples.
Keep development incidents separate from final testing. Treat multiple attempts
on the same incident as repeated measurements, and calculate uncertainty at the
appropriate incident/repository level. A small pilot supports feasibility, not
precise population estimates or claims of negligible residual risk.

### Prior work and the proposed difference

The access question already has a policy and statistical foundation in
[Cen and Alur's discussion of access and evidence in AI auditing](https://arxiv.org/abs/2410.04772).
The proposal operationalizes a narrower version for executable agent evaluations.

[BenchShield](https://arxiv.org/abs/2609.11028) studies infrastructure evidence and
reward integrity across an evaluation lifecycle. Its results rule out treating
"add provenance to evaluation scores" as a fresh contribution. Use its integrity
categories and, where practical, its evidence as inputs or baselines.

[Who Audits Whom](https://arxiv.org/abs/2609.18272) distinguishes independence of
principals, substrates, and evidence, with structural analysis and simulation.
The proposed study must add measured interventions on executable incidents and
real auditors, rather than rename those distinctions.

[Actions with Receipts](https://arxiv.org/abs/2610.00327) binds claims, sources, and
execution records and separates structural integrity from semantic support.
Receipt construction alone is therefore insufficient as a novelty claim. The
experiment asks which evidence rights resolve which claims and what errors remain.

This literature review supports a candidate contribution, not a claim of being
the first. Before a paper submission, compare complete experimental protocols
and released implementations against this proposed access-ablation study.

### Open-source release

Ship a small Python package, an Inspect adapter, reproducible incident generators,
typed evidence bundles, access-policy enforcement, and deterministic baselines.
The access policy must be enforced by the harness: hiding an artifact's pathname
in a prompt is insufficient if an audit tool can still read it. Keep labels and
reference witnesses outside the auditor's filesystem and tool responses.

A useful first release lets a maintainer export one evaluation claim, restrict
which evidence is disclosed, run an auditor, and replay its cited witness. Include
a no-key scripted demo and an optional model-backed evaluation with explicit cost
limits. Every published figure should be reproducible from versioned run records.

Build the first full slice around the existing ledger task, then add an unrelated
repository and an aggregate-reporting scenario. Expand only after the baselines
work and reviewers can distinguish missing evidence from poor reasoning.

The main risks are artificial incidents, answer leakage, and defining access
conditions that make the conclusion true by construction. Counter these with
ordinary honest failures, natural evaluation artifacts, human review, and a held-out
incident family. A strong null result would be that simple deterministic checks
resolve nearly everything; that would favor a smaller practical verification tool.

## Option 2 Safety controls under ordinary maintenance

**Research question:** How often do coding agents weaken operational safety
controls while successfully completing legitimate maintenance work, and which
review mechanisms preserve both task usefulness and control effectiveness?

Start with an agent service containing executable controls: scoped tool access,
approval checks, audit logging, fail-closed behavior, and a restricted data boundary.
Give a coding agent a sequence of ordinary tickets such as reducing latency,
handling a provider outage, upgrading a dependency, or reducing log volume. Every
ticket must have a valid reference solution that preserves the security contract.

After each accepted change, run functional tests and independent adversarial
probes. A failure might appear when an availability fix allows actions after the
approval service times out, even though the ordinary feature tests remain green.

Compare isolated maintenance tasks against cumulative sequences, with matched
tasks and randomized ordering. Compare prompt guidance, a code-review monitor,
and an external invariant-testing gate. Measure task completion, control failures,
time to the first failure, unnecessary rejections, and review cost. Keep an
explicitly malicious-agent condition separate if added later; ordinary mistakes
do not demonstrate deceptive intent.

The principal figure would show control survival over accepted changes alongside
useful work completed. An open-source release would provide persistent maintenance
environments and reusable control-regression probes.

[Distributed Attacks in Persistent-State AI Control](https://arxiv.org/abs/2607.02514)
already studies covert attacks spread across successive changes.
[SlopCodeBench](https://arxiv.org/abs/2603.24755) measures code degradation under
iterative development. The proposed distinction is ordinary maintenance of the
safety infrastructure itself, scored by whether explicit controls still stop
specified actions. This distinction needs to survive a deeper protocol comparison.

This direction has a strong AI-control story and a compelling demo. Its main
cost is building realistic maintenance sequences and controls whose effectiveness
can be checked independently. An unrealistic ticket that practically instructs
the agent to remove a safeguard would provide weak evidence.

## Option 3 Evaluation integrity regression tests

**Research question:** Which commonly used scoring assumptions fail under small,
reproducible adversarial changes, and which fixes preserve legitimate solutions?

Turn the pilot into an Inspect-oriented conformance suite. Each fixture states
the allowed artifact changes, expected task outcome, observed native score, and
the trust boundary crossed. Run the suite before and after scorer changes to
catch false positives and false negatives. Include tests for clean early exits,
module substitution, missing results, stale result files, and artifact mismatch.

The open-source product would be a useful CI integration for evaluation authors.
Record an explicit inconclusive result when the evidence cannot support a score;
do not silently translate infrastructure failure into task success or failure.

The research novelty is lower. [BenchJack](https://arxiv.org/abs/2605.12673)
already discovers and patches benchmark exploits, and
[RewardHackBench](https://github.com/islo-labs/reward-hack-bench) compares sandbox
policies against cheating opportunities. A defensible contribution would need to
show adoption value, broader regression coverage, or a measured improvement over
those baselines. This is the best fallback for a compact engineering release and
a useful component of Option 1.

## Recommended scope

Pursue Option 1 as the flagship research question, using a small part of Option 3
to generate and validate incidents. Choose Option 2 instead if the primary aim is
an empirical AI-control project centered on coding agents. Combining all three
into the first release would obscure the experimental question.

The release should contain one clear claim, an executable reproduction, honest
baselines, uncertainty estimates, and a documented way to contribute a new incident
family. Keep any fellowship application materials outside the public repository.
Before public release, add an appropriate open-source license, contributor guidance,
dependency locking, CI, and citation metadata. These are release deliverables;
the current pilot and proposal are the first completed artifacts.
