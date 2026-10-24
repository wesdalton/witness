# One query credit can contain exhaustive computation

The free post-hoc work audit confirms a limitation of the current effort measure:
all SQL statements cost one query credit, but their computational work differs
greatly. On their observed databases, the eight one-query route verifiers used
1K–8K nominal SQLite progress units; the four schedule verifiers used 2K–178K.
All returned correct exact answers. This does not invalidate their finite scores,
but it prevents interpreting a one-call allowance as a small fixed amount of
verification work or as an information bottleneck.

The instrument keeps the original sandbox and progress limit. It records progress
callback counts multiplied by 1,000 on SQLite 3.46.1. These are approximate work
units, including possible preparation work, not exact instruction bounds, time,
API charges, model reasoning effort, or human effort. This qualification follows
the [SQLite progress-handler contract](https://www.sqlite.org/c3ref/progress_handler.html).
The first artifact's field names overstated precision; its values and source remain
unchanged with a separate [adjudication](query-work-adjudication.json). The corrected
[measurement](query-work-measurement-v1.json) records the limitation and version.

## Free deterministic improvement

All four schedule programs use recursive UNION ALL. They carry every
future-relevant state component: executed-operation set, shared balance, and each
worker's saved register. Two also carry a redundant depth counter. Reaching the
same complete state through several histories creates identical possible futures.
For MIN over terminal balances, multiplicity has no effect on the answer.

Replace only that recursive UNION ALL with UNION. State reachability is unchanged:
inductively, identical states have identical legal successors, and duplicate
removal neither creates nor removes a reachable state. Termination follows from
one new operation per transition. The argument is specific to these reviewed
queries; it does not authorize arbitrary SQL rewriting, schedule counting, or
omitting path-dependent information.

On the already-declared four-worker zero-delta boundary:

| Program | Original nominal units | Deduplicated units | Original / changed |
| --- | ---: | ---: | ---: |
| Episode 001 | 1,600,000 | 40,000 | 40.0 |
| Episode 002 | 1,088,000 | 21,000 | 51.8 |
| Episode 003 | 1,107,000 | 22,000 | 50.3 |
| Episode 004 | 1,107,000 | 22,000 | 50.3 |

All four transformed programs retained correct results on all sixteen replay
conditions each. The [ablation artifact](query-efficiency-analysis.json) preserves
original hashes, changed SQL, exact implementation snapshots and every result.
Original agent programs and their scores remain unchanged. This is a deterministic
local optimization demonstrated without another API request, not a 40–52× model
speedup, a population effect, or a novel algorithm.

The result suggests separating semantic adequacy, computational efficiency, and
query acquisition in future studies. It does not justify lowering the resource
limit until agents fail. A future constraint needs an independently motivated cost
model and a demonstrated opportunity cost, rather than a call count chosen as a
proxy for difficulty. A larger social comparison on the current ceilings is not
selected.
