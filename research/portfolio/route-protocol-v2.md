# Prospective numeric-domain repair; no new paid batch selected

After the fixed 32-episode interface screen completed, free boundary review found
that the v1 route contract permitted integer edge costs without an upper bound.
Four edges of cost 3,000,000,000,000,000,001 yield an exact pair optimum of
12,000,000,000,000,000,004. The SQL reference instead returns the floating value
1.2e19. Such an exact optimum cannot be returned as one SQLite INTEGER under the
old output contract. This is a harness/specification defect, not a model failure.

All observed experimental and frozen replay graphs use small positive costs and
have independently matching exact integer answers. Preserve their finite claim
and replay scores; do not infer universal correctness from those finite passes.
Keep every original prompt, reference snapshot, result, and protocol unchanged.
The numeric counterexample and scope adjudication are separate artifacts.

Contract revision 2 restricts each edge cost to an integer from 1 to 1,000,000.
With at most ten nodes and acyclic paths, even the loose bound of eighteen edges
across two paths gives a total no larger than 18,000,000, safely within exact
SQLite integer arithmetic. The host validator checks node/edge/risk domains,
acyclicity, at most ten nodes, and at most 64 source-to-sink paths before creating
the database. Model-written SQL continues to run only in the isolated driver.
Schema and graph semantics otherwise remain unchanged. The runner records the
contract revision in future manifests; v1 remains reproducible from its snapshots.

Free gates test maximum costs and rejection of oversized costs/cycles, alongside
the existing graph/reference/mutation checks. A new paid study still requires a
separate justified question, frozen sample, maximum reservation, and decision.
The completed mandatory-program and output-requirement screens are ceilings
under the tested conditions; a larger replication is not selected merely to spend
the remaining budget or to obtain a desired effect.
