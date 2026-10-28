# Research decision log

## Gate 0 — free infrastructure checks, 24 October 2026

83 Python tests and lint passed before paid requests. Live Docker probes produced
the expected inclusive results for the corrected case and exclusive results for
the broken case. Tests confirmed an unprivileged UID, absent API credential,
read-only source, unavailable network, bounded returned output, and cleanup after
timeout. The provider credential is available and its non-resetting cap is $100;
the additional local phase ceiling is $25. The first batch ceiling is $0.50.

Decision: buy four calibration episodes on GPT-6 Luna with reasoning disabled.
This is enough to expose basic tool/context failures before a treatment matrix.

## Gate 1 — first calibration stopped after two requests

`luna-calibration-01` spent $0.0001471. The model listed files and then requested
three reads together. The harness rejected multiple calls per response. No live
Python or final verdict occurred. This is a harness restriction, not evidence
that the agent cannot verify. Remaining planned episodes were not dispatched.

Improvement before spending again: accept native tool bundles, validate the
entire bundle first, charge each action, assign distinct evidence IDs, and forbid
submission in the same response as an unobserved tool. Add regression tests and
retain the failed attempt separately. Restart calibration under protocol v0.2.
The research question and case family remain unchanged.

## Gate 2 — calibration passed; buy one small treatment screen

`luna-calibration-02`: four completed episodes, 12 requests, $0.001778025 reported
cost. Every episode read source and reached the correct verdict; one also ran
the supplied tests. Transcript review confirms that the `<` / `<=` predicate
provides adequate direct evidence here. No agent-written Python was necessary.
Do not describe absence of Python execution as failure to verify.

The task is easy and baseline acquisition is at a ceiling. The cheapest useful
next question is whether endorsements change that baseline. Run the previously
specified 16-episode four-arm screen with a $0.50 reservation ceiling. No increase
in population, model price, or case difficulty yet. If acquisition remains at a
ceiling across arms, stop repetitions of this setup and record the null screen.

## Gate 3 — ledger screen is at a ceiling; stop repeating it

`luna-screening-01`: 16/16 completed, acquired source evidence, and reached correct
verdicts, with four episodes per arm. One executed supplied tests; none needed
agent-written Python. Cost: $0.006072840. Cumulative phase cost: $0.007997965,
including the failed first calibration. The frozen-source, event-trace, response-ID,
and usage audit passed. The first aborted batch has configuration/hashes but no
full source snapshot; preserve that provenance limitation.

Decision: do not purchase more ledger repetitions or a model sweep on this easy
case. There is no observed acquisition contrast to explain. The effort budget
also has no competing payoff, so it does not operationalize communication
displacing useful work. Those are design limitations, not evidence against all
versions of the hypothesis.

Cheapest next useful observation: can the agent write and execute a correct
verification query when inspecting a short source function cannot settle the
claim? Add a separate SQLite aggregate-report family and validate it for free,
then run four no-peer calibration episodes under protocol v0.3. This tests a
missing capability and adds a distinct case family without tuning for mistakes.

## Gate 4 — agent-written execution works; redesign before more inference

`luna-sqlite-calibration-01`: four completed episodes, 16 requests, $0.001719900.
Each agent independently wrote a parameterized SQLite query through the Python
tool. Queries filtered account `ops`, used both inclusive date endpoints, and
returned 43,210 or 42,310 as appropriate. All four verdicts matched the live
result. The agent saw no reference query or expected total beyond the disputed
publisher's claim. Manual review found these executions relevant to the claim.

Cumulative phase: 78 requests; 24 completed audits plus one retained interrupted
calibration; $0.009717865 reported charges; $0.132148625 retained conservative
reservations. The $25 ceiling is neither reset nor treated as a spending target.

Decision: end this research cycle without buying a second-model sweep or another
single-claim screen. We have established live source acquisition and live
agent-authored verification, not communication displacing verification. The next
study needs competing claims and an actual opportunity cost. Develop and validate
that environment before more paid inference; see next-experiment.md. There is no
scientific reason to spend the remaining allocation merely because it is available.
