# Witness v0.1: executable model and measurement notes

This document describes authored simulation rules, not fitted LLM behavior. The
browser and Node CLI import the same `website/dist/engine.js` implementation.

## State and sources

Agent i has a modeled probability p_i that a positive claim is true, a source ledger,
a directly-checked flag, and an optional pending verification. Initial beliefs are
0.5 without information, 0.82 after the positive report, and 0.99/0.01 after a direct
probe (depending on truth). Fractions selecting initial report/probe recipients are
independent seeded Bernoulli draws; they are not exact quotas.

All copies of the success report have root `report:0`. Every retrieval of the same
recorded behavioral test has root `probe:0`. Different agent IDs, messages and
requests do not create independent evidence. The ledger can retain at most 12 roots,
prioritizing verified roots; this release has only two possible roots.

Truth is either false (the shadowed runner reports success on a buggy patch) or true
(the honest fixture). An already directly checked agent retains the true result.
This absorbing-grounding assumption favors eventual correction and excludes some
forms of forgetting, deception, and distrust. Receiving a probe by relay and directly
requesting it are separate events.

## Graph and scheduling

All graphs are undirected with a ring for connectivity. Small-world graphs add local
second neighbors and random shortcuts. Modular graphs add mostly within-community
links; hub graphs connect nodes to a small set of hubs. These are lightweight graph
families, not exact canonical Watts–Strogatz or stochastic-block implementations.
The layout is illustrative and does not encode graph distance. At large populations,
only displayed edges are sampled; all agents and graph links participate in updates.

Each round reads the preceding round's snapshot. A due probe is applied to its
recipient before that recipient acts; peers see it in the next snapshot. A check
requested in round r arrives in r + delay (immediately if delay is zero). There is no
within-loop cascade that rewards agents processed early.

## Resource allocation

Every agent spends four abstract effort units every round. A check costs four units;
otherwise the agent reads four messages, one unit each, sampling neighbors with
replacement. Multiple slots can read the same neighbor. Pending or already checked
agents still read messages. Sending overhead is not separately charged.

With communication preference c and confidence q_i = 2|p_i - 0.5|:

- Fixed allocation: check probability = 1 - c.
- Adaptive allocation: check probability = (1 - c)(1 - 0.85 q_i).
- Reserved-checking policy: check probability = max(0.15, 1 - c).

These rules apply only if the agent has neither checked nor requested a pending
check. The adaptive confidence–checking relationship is **assumed**, not established
by this simulation. Compare against fixed allocation to expose that assumption.
Initial probes are endowments outside the round budget; match them across policies.

Accounting identities are checked in tests: effort = 4 × population × round =
messages + 4 × requested checks. Requests equal completed + pending + canceled
requests. An injected correction can cancel a pending check without refunding cost.

## Belief updates

For peer-endorsement pooling, let m be the average belief in the four sampled
messages and g be the social reinforcement slider (default 6). Then:

    social = 1 / (1 + exp(-g * (m - 0.5)))
    p_next = clip(0.55 * p_previous + 0.45 * social, 0.01, 0.99)

This nonlinear gain can reinforce majorities. Lowering it can dissolve a cascade;
the gain is exposed precisely because the result depends on this modeling choice.
The endorsement policy stores source metadata for inspection but ignores it when
updating belief. A directly checked agent's belief remains grounded.

For source-aware and reserved-checking policies, a verified root sets p to 0.99 or
0.01. Without a verified root, sum one signed log-odds contribution per distinct
root, each of magnitude log(0.68/0.32), clip total log odds to [-4.6, 4.6], then apply
the logistic function. Repeating the positive root leaves p at 0.68; it does not
raise confidence. This is an illustrative deduplication rule, not a validated
Bayesian model of arbitrary evidence. In particular, one source-aware agent can
still be wrong, and trusted probe metadata has strong built-in value.

## Metrics and comparisons

Support means p >= 0.65; refutation means p <= 0.35; intermediate beliefs are
uncertain. Correct/mistaken refer to the configured truth, not to the majority.
Brier score is the mean squared probability error. Probe reach counts possession
of a probe root, including relayed copies; completed checks count requests fulfilled.
Neither metric counts independent probe roots beyond the one available in this task.

Policy comparison uses the same graph, initial exposures, seed, and per-round effort.
It changes the policy, including its belief update and (for reserved) allocation.
It is not an isolated causal estimate of provenance alone. Time-averaged error,
peak error, uncertainty and checking effort expose differences that terminal accuracy
can conceal. Longer runs can converge even after a substantial transient error.

Injecting a correction gives a definitive probe to a deterministic 1% sample of
agents (rounded up, minimum one). It may select agents who already have the result.
It is an external information intervention, explicitly outside the effort budget.
The chosen IDs and round are included in exports. Repeated clicks are separate events.

## Reproduction and limits

Exports contain configuration, engine version, assumptions, interventions, trajectories
and final agent summaries. The seeded generator is an engineering reproducibility
mechanism, not a cryptographic generator. Exact same-runtime runs match; floating-point
math can differ by tiny amounts between browser and Node engines. Replay should
require identical discrete decisions and permit only documented numeric tolerance
for belief/Brier fields. Changing an algorithm requires a versioned artifact.

The recorded 540-run sweep crosses 10 seeds, two truth values, three graph families,
three policies and three communication preferences. Its synthetic variability is
not uncertainty about real LLM behavior. No parameters have been estimated from LLMs.

The Python harness has a different purpose: measure actual policy decisions. It
uses recorded tool observations, a total per-agent action budget, one-recipient
relays, a retained latest direct probe plus recent-evidence context and a provider-independent policy interface. It
records actual model usage separately from abstract action effort. It does not
force an LLM to retain or obey a verified result. Inspect is an optional provider
adapter; browser simulation and scripted harness runs need no API keys. From harness
v0.2, graph construction and report seeding draw from independent random streams,
and a positive report share always seeds at least one agent.

## Recorded default example

With seed 42 and the release defaults, peer endorsements reach 32.0% peak mistaken
agents and 7.0% mean mistaken agents; source tracking reaches 82.8% and 9.5%,
respectively (rounded). Both finish at zero mistakes. The arithmetic mean includes
round zero and all 60 subsequent snapshots. In this authored example, tracking a
shared false root can spread a moderate but still incorrect belief before a probe
arrives. This is a consequence of the stated rules, not evidence that provenance
harms real agents. It illustrates why the interface reports transient error and
costs rather than presenting a selected favorable endpoint as a success story.
