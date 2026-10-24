# Next experiment: allocation of verification across competing claims

Design draft after the 24 October pilot. Not implemented or run. Freeze a final
protocol and pass the free validity gate before dispatching further model calls.

## What the first cycle changed

The ledger screen showed no acquisition difference: all 16 auditors read source
and answered correctly. The SQLite calibration established agent-written execution
in four additional episodes. Neither task gave an agent a reason to conserve
effort for another claim. Repeating them more times or using more expensive models
would not repair that missing mechanism.

The next question is whether repeated endorsements redirect a finite verification
budget away from the endorsed claim, when unused effort can instead verify other
claims. It is about allocation, not whether a model can follow an instruction to
run a test.

## Proposed environment

An auditor submits decisions for a portfolio of six claims. The score weights
every claim equally and uses proper probability scoring, with verdict/error
coverage reported separately. It can obtain live evidence for only a subset of
the claims. Agent-written code runs in a separate case workspace per request;
one request cannot inspect multiple cases through a shared host filesystem.

Use at least three independently authored case families before a model comparison:
transaction reconciliation, configuration/runtime behavior, and data-transform
correctness. True/false variants within a family are paired cases, not independent
families. Verify honest and incorrect variants offline, and include an easy case
where checking is not useful so that indiscriminate verification has a cost.

Begin with one common, enforced unit per case investigation and verification
budgets of two, four, and six investigations. Report API dollars, latency, input
tokens, and execution time separately. This is a designed resource constraint;
do not call action units measured real-world expense. Source access must either
share this budget or be deliberately free and recorded: it cannot be an uncounted
route to all answers.

## Treatment assignment

Create a portfolio with an identical underlying case set and reports for each
matched condition. Randomly select the target claim independently of truth,
difficulty, account/date values, position, and case family. Keep target selection
out of the agent's metadata. Supply either neutral peer statements, repeated
endorsements of the same report, or those endorsements with the shared root
disclosed. Include a no-peer baseline, but use the neutral-message comparison to
reduce the confounding effect of merely adding context.

Peer statements remain authored stimuli for causal control. Independent live
peers come later, after establishing that the local allocation response exists.
Do not claim emergent multi-agent behavior from this intervention.

Randomize portfolio position and presentation order. Match message lengths with
the deployed tokenizer where feasible, while recognizing that wording and
provenance disclosure carry semantic information. Avoid peer model-family labels
until identity effects are explicitly part of the study.

## Outcomes and cheap decision gates

The primary endpoint is the probability of allocating a live investigation to
the target claim. Secondary outcomes include where the saved investigation goes,
portfolio Brier score, false acceptance, abstention, and the quality of the
agent-written checks. Count attempts, useful executions, and failed executions
separately. Correct source reasoning is evidence even when no process executes.

1. **Free:** prove that budgets bind, cross-case access is impossible, truth is
   hidden, and reference checks recover all case labels. Test deterministic
   baselines (no checks, random allocation, all checks) and scoring arithmetic.
   Derive detectable effect sizes and the maximum precision the affordable pilot
   could achieve; do not claim adequate statistical power from a small call count.
2. **Small capability calibration:** at most six portfolios on the economical
   model. Inspect every attempted investigation. Stop if the model cannot use the
   tools or if the budget restriction is illusory.
3. **Allocation screen:** choose sample size only after estimating actual calls,
   variance, and tool failures from calibration. Freeze contrasts and allocation
   in advance. Treat portfolio/case draws, not turns, as the observational units.
4. **Replication:** only if the screen produces a useful, interpretable contrast,
   test new case instances and a second model. Report a null or beneficial effect
   just as plainly as a harmful effect.

Each paid stage needs a written expected-information argument and a maximum
reservation within the remaining phase budget. A new prompt, case family, scoring
rule, or model configuration gets a new version and separate results. No hidden
post-hoc selection of peers, errors, or favorable examples.
