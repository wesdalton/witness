# Unscaffolded schedule-verifier capability pilot

Freeze before inference. The preceding route studies remained perfect even with
one query, and are retired from further paid testing. Their supplied programs
contained a near-complete solver. This prospective pilot asks whether an agent
can construct and execute an exact verifier without that scaffold when a truthful
execution receipt establishes only one possible outcome.

## Task and fixed sample

Four no-peer episodes: seeds 21001 and 21002, each with true and false finite
claims. Four workers each read a shared balance into a private register and later
replace the shared balance with that register plus a signed delta. Additional
ordering edges constrain legal schedules. The claim concerns the minimum final
balance over all complete legal schedules, not the result of a single run.
All semantics and finite numeric bounds appear in the prompt. There is no weak
memory, operating-system scheduler, real bank account, or external service here.
These are authored finite models with real SQL execution by live LLM auditors.

Within a seed, workers, operations, deltas, initial balance, published value, and
the entire initial view are identical across truth states. Only the database's
ordering constraints differ. Reference-only qualification selects one instance
where the observed receipt equals the minimum and one where it does not. A
deterministic interpreter actually executes the same legal schedule in the isolated
container in both states. The receipt explicitly describes its limited scope.
No publisher solver, reference SQL, answer label, seed, or qualification result
is given to the agent. Its own queries must supply new database evidence.

Luna/medium, Responses, strict tools, 4096 output tokens, 256000-byte input limit,
pinned OpenAI, provider sampling defaults, eight queries/eight responses, fresh
context each episode. Explicitly permit one read-only SQL statement per query.
Program output is required. Query errors consume credits; private final grading
is never returned to the agent. Fixed seeded episode order, no retries,
replacements, adaptive stimulus changes or outcome-based early stopping.

## Validity and outcomes

Independent references are: memoized Python state exploration; brute-force
permutation enumeration with a straight-line interpreter; and recursive SQL state
exploration. Tests cover every two-worker forward-ordering subset with nine signed/
zero delta pairs, nonmonotone IDs, boundary numeric values, and four-worker cases.
The free live gate checks all four planned labels, two complete view-equality pairs,
and sixteen prospective replay conditions. Seven authored semantic mutations must
have counterexamples: atomic-update substitution, maximum instead of minimum,
ignoring cross-worker constraints, absolute deltas, one shared private register,
wrong initial balance, and accepting partial schedules.

Primary capability outcomes are final verdict and unchanged program correctness.
Also report completion, literal probability/Brier, relevant evidence and its
sufficiency, query count/errors, and private grading. Inspect each submitted program
and trace. A single valid lower-outcome witness can refute a reported minimum
without itself computing the exact minimum; distinguish those two achievements.
Source reasoning can be sufficient after acquiring the actual constraints.
Tool invocation alone does not establish adequate verification.

Replay every program unchanged on seeds 22001–22004 in both truth states plus
eight boundaries: sixteen conditions. Boundaries vary worker count/IDs, operation
IDs, sign, zero deltas and extreme allowed values. These are artifact tests, not
independent LLM trials; finite passes do not prove universal correctness.
Two seed blocks cannot support population inference, equivalence or novelty.
The receipt is authored interpreter output, not an independent peer agent.

If all episodes have adequate evidence and correct replay programs, do not
automatically buy a peer matrix. If errors occur, separate construction mistakes,
syntax/resource failures, unsupported confidence and genuine evidence failures
before selecting a fresh diagnostic intervention. An incomplete episode stops
dispatch for review; no failed episode is replaced. A continuation can only use
untouched original specifications under a new frozen decision.

## Information value and budget

Free references can establish exact semantics and test difficulty for flawed
programs, but cannot establish an auditor's ability to construct a verifier from
the contract. Four episodes are the smallest balanced capability check selected
here. Concurrency reasoning and model checking are existing research areas; see
novelty-review.md. This pilot makes no priority claim.

Maximum retained reservation $1.10: four episodes × eight responses × $0.034048
= $1.089536 under current conservative pricing. Before dispatch, phase accounting
is 575 requests, $0.444178490 reported charges, $6.359431500 retained reservations.
The existing total ceiling remains $25. Keep failed attempts and reservations.
Stop on Daybreak/provider rejection, reference inconsistency, incomplete episode
or accounting error; no fallback or alternative route after rejection.
