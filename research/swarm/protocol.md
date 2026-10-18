# Witness: when communication displaces verification

Wesley Dalton · protocol v0.1 · literature checked 18 October 2026

**Status: research prototype, not a completed empirical study or preregistration.**
The release contains a mechanistic browser model, executable grounding fixtures,
and a bounded experiment harness. Initial real-model trajectories have been collected
as an infrastructure pilot; see the [pilot report](pilot-report.md). The hypotheses
below remain proposals. Neither the authored demo nor this small pilot establishes them.

## The question

Under a fixed resource budget, when does communication among AI agents reduce the
collection of independent evidence, and when does that tradeoff harm collective
accuracy? Can evidence ancestry or a small verification allocation prevent the harm
without destroying the benefits of coordination?

The candidate contribution is an **experimentally identified feedback loop between
peer agreement and evidence acquisition**, evaluated on grounded tasks. Many agents
can repeat one report. Agreement may then reduce the incentive to check, leaving
less fresh evidence to challenge the agreement. This mechanism is plausible, not
yet observed here. It may be weak, absent, or beneficial when reports are accurate.

We study deployed AI systems as systems, rather than claiming that their messages
reveal human-like social motivations. Politeness, trust, and sycophancy are possible
behavioral descriptions, not explanations inferred from fluent dialogue. Attributing
an effect to RLHF would require an appropriate checkpoint/training comparison.

## Where this sits in current work

| Prior work | Established territory | Implication for Witness |
|---|---|---|
| [Physics of Agents, 2026](https://arxiv.org/abs/2608.16578) | Predictive collective dynamics across over 10,000 communities, including truth-seeking on objective tasks. | Consensus regimes and graph generalization are not new claims. Test whether evidence acquisition adds predictive value. |
| [Epistemic Sybil Resistance, 2026](https://arxiv.org/abs/2609.01873) | Multiple reports need not represent independent evidence; source dependence matters for aggregation. | The closest evidence baseline. Merely tracking roots is insufficient novelty. |
| [Delayed Verification, revised September 2026](https://arxiv.org/abs/2606.27409) | Delay can destabilize signed-belief dynamics, while grounded factual answering eliminates the reported oscillation. | Grounded evidence may stabilize this system. Do not generalize its oscillation result to our task. |
| [Lie Rarely, Lie Big, October 2026 preprint](https://arxiv.org/abs/2610.04744) | Grounded robot teams face costly verification and insider misinformation. | Verification opportunity costs already have direct prior art. Distinguish endogenous checking from adversarial allocation. |
| [Too Polite to Disagree, SIGDIAL 2026](https://arxiv.org/abs/2604.02668) | Peer sycophancy information can change influence and discussion outcomes. | Compare ancestry with peer-reliability information; do not rename sycophancy propagation as a discovery. |
| [Emergent Social Conventions, 2025](https://arxiv.org/abs/2410.08948) | Conventions and collective biases emerge in LLM populations. | Group-level behavior need not be predicted by isolated-agent tests. |
| [AgentSociety](https://arxiv.org/abs/2502.08691), [OASIS](https://arxiv.org/abs/2411.11581) | Large social simulations already reach thousands to a million agents. | Population size is an engineering dimension, not our novelty claim. |

These are primary sources, including recent preprints whose claims may change.
The distinction above is a proposed research position, not proof of priority. A
submission should refresh this review and replicate the nearest feasible baselines.

## Grounding and threat model

The first task asks whether a patch fixes a ledger. Two authored fixtures return
identical success reports; only one fixes the behavior. A separate recorded probe
compares an observed balance and statement length against an explicit reference.
The pilot reproduces the scorer decision locally, not through the full original
Inspect/Docker pipeline. It demonstrates an evidence ambiguity, not model misconduct.

Repeated access to the same recorded probe remains one evidence root. Re-running
the same deterministic test is not an independent source merely because another
agent requested it. An evidence root denotes an observation process with declared
dependencies, not a speaker or a unique message ID.

The release assumes authentic, unforgeable root metadata and a definitive probe.
Those are favorable conditions for ancestry-aware policies. Future experiments must
also include incomplete provenance, forged provenance, noisy probes, conflicting
independent observations, and unavailable verification. A trusted receipt is not a
proof that its measurement procedure is valid. The current verifier is not a secure
sandbox for arbitrary submissions.

## Hypotheses and falsification

1. **Acquisition feedback:** holding evidence roots fixed, additional agreement
   reduces the probability of requesting a check. Falsified if checking is unchanged
   or increases across controlled, held-out exposures.
2. **Opportunity-cost harm:** with a fixed budget, the communication increase raises
   error by reducing useful verification. A correlation between agreement and error
   alone does not support this mechanism.
3. **Ancestry intervention:** identifying shared roots attenuates that effect. It may
   instead merely improve static aggregation, which is an informative narrower result.
4. **Allocation intervention:** reserving some checking effort reduces integrated
   error on false reports at an acceptable cost on true reports. The intervention
   fails if it wastes resources without improving the accuracy–cost frontier.

A null result is publishable if measurement is reliable: e.g. grounded tool access
makes the proposed cascade disappear. Do not optimize the task until it yields harm.

## Experimental sequence

### Stage 0 — infrastructure, implemented

The browser uses authored belief/allocation equations. It supports controlled graph,
source, delay, and allocation changes; deterministic seeds; policy comparisons;
recorded corrections; and exports. It is useful for falsifying implementation bugs
and exposing assumptions, not for measuring an LLM population.

The Python harness runs synchronous, bounded model decisions on the matched fixture
pair. Agents choose check, relay, or abstain and report a probability. It provides
report-only, ancestry-visible, and reserved-checking treatments. The latter forces
and charges one check per agent on the first turn. This is deliberately a simple
infrastructure baseline; it differs from the browser's per-turn reserved probability.

The runner logs model outputs, visible observations, source IDs, actual token usage
when supplied by the provider, invalid decisions, and action costs. Its recorded
probe is returned after a delay; it does not run a new sandbox per request. Current
context is bounded to recent receipts. Scientific use must analyze that memory limit.

### Stage 1 — identify a local response, proposed

Use 24 or more independently constructed case families spanning test reports,
retrieval claims, and configuration/security checks. Balance true and false claims;
include correct reports where checking wastes useful budget. Do not count two
variants of the same ledger bug as independent tasks.

At a frozen agent state, randomize three factors: number of endorsing peers, number
of independent roots, and whether ancestry is visible. Keep report content quality,
length, agent role and available checking budget matched. Use repeated draws rather
than claiming deterministic generation from a provider seed. Include disagreement
and no-peer controls. Estimate the change in check probability before closing the
feedback loop.

This branch experiment distinguishes social exposure from evidence abundance. The
current release has the event/view boundary needed for it; automated branching and
factorial episode generation are future work.

### Stage 2 — close the feedback loop, proposed

Start with 16–64 agents and three model families. Cross topology, evidence policy,
verification delay, and resource budget. Use matched cases, graph seeds and initial
exposures across arms. Compare endogenous checking with fixed/random checking and
reserved allocations. Include a single-agent verifier and independent ensemble.

Measure both equal resource ceilings and comparable realized expenditure. Action
units are not API dollars: report token counts, latency, calls and tool costs
separately. If savings fund more generations in an arm, make that a separate study.
Use the same model-call envelope and truncation policy where possible; report invalid
responses and exhausted budgets instead of silently removing them.

To identify mediation, replay matched evidence opportunities under an externally fixed
checking schedule. If the communication penalty persists with checking opportunities
held fixed, acquisition alone cannot explain it. Prompt wording and information
exposure must also be controlled; a larger message count can change the available
information independently of checking.

### Stage 3 — fit and test system dynamics, proposed

Fit a transition model for checking and belief revision from Stages 1–2. Compare it
with a constant-rate model, simple averaging, and ancestry-aware aggregation. Split
by case family, graph and model rather than random individual messages. Test
out-of-sample trajectories and recovery times, not just fit to training curves.

Only after held-out validation should the fitted process be simulated at 10,000
agents. Label that result an extrapolation, with sensitivity to parameter uncertainty.
The current 10,000-node demo is an authored model, not such a calibrated forecast.

## Outcomes and statistical commitments

Primary outcomes: time-averaged fraction of mistaken agents; independent evidence
acquisitions per budget; and the effect of randomized endorsement count on check
probability. Secondary outcomes: Brier score, abstention/uncertainty, peak error,
false-consensus duration, source concentration, and recovery after correction.

Report correct, incorrect and uncertain agents separately. A reduction in false
consensus achieved by making everyone uncertain is not necessarily an improvement.
For recovery time, define a threshold in advance and report non-recovery as censored,
not as zero. Free external corrections are separate interventions and add information
outside the nominal budget.

The independent unit is a case/seed episode, not a message or agent in the same
connected run. Use paired differences and cluster-aware uncertainty across case
families. Predefine exclusions, invalid-response treatment, primary contrasts and
multiplicity handling before confirmatory runs. Pilot variance informs a power
analysis; do not invent a sample size or significance claim from synthetic curves.

## What would justify calling this a flagship result?

A reproducible release is the foundation. The research contribution needs a reliable
measurement of the acquisition feedback, evidence that the feedback matters for
accuracy under realistic costs, an intervention with quantified tradeoffs, and a
held-out test showing the explanation predicts something new. Publish negative
conditions and failure cases alongside any successful intervention.

The current artifact supports a claim of having built and tested an
open-source research instrument. It does not support claims of discovering a new
social law, outperforming current methods, or demonstrating 10,000 real LLM agents.
