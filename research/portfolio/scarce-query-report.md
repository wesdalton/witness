# One-query pilot: another clean ceiling

All eight live agents completed correctly using exactly one query each. Every
first query enumerated all admissible path pairs and computed the true optimum;
two also returned witness paths or diagnostic counts. All eight final programs
passed the thirty frozen fresh conditions each. No syntax failure, invalid action,
probability-direction contradiction, or evidence/justification gap was found.
Mean Brier loss was 0.00002575.

The [frozen pilot](scarce-query-protocol-v1.md) used four fresh seed blocks in both
truth states, no peers, program output, contract v2, and identical initial evidence
across truth states. It tests capability under a known resource limit. Differences
from historical runs include the budget, the numeric contract repair, and an
explicit single-statement instruction; they prevent a causal budget comparison.
The eight judgments share four blocks, while 240 replay executions evaluate eight
programs rather than 240 additional agents. Finite passes are not a proof for all
possible inputs.

The narrow conclusion is useful: additional inspection calls were unnecessary
for these fresh cases when the agent knew it had one query. The observed success
does not establish resource-insensitive auditing in general. The supplied greedy
program already contains the complete path-enumeration machinery; repairing the
pair-selection clause is a substantial scaffold. The task has interacting
constraints, but has not demonstrated hard independent verifier construction.

Sixteen requests added $0.006264455 reported cost and $0.059706500 retained
reservations. Phase totals are **575 requests, $0.444178490 reported charges,
$6.359431500 reservations**, against the same $25 ceiling. No retries, replacements,
fallbacks, or Daybreak rejections occurred in the visible outputs.

Decision: retire this route setup from further paid testing, including a new
peer matrix or another budget escalation. The next free development step should
require construction of a verifier without a near-complete supplied algorithm,
and validate the task with independently implemented exact semantics first.
Concurrency schedule outcomes are a candidate, not an established novel task:
existing work already studies LLM concurrency analysis and formal verification.
