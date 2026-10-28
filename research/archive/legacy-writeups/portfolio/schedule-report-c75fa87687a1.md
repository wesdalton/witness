# Unscaffolded schedule verification: four correct live audits

All four live agents completed with correct verdicts and correct executable
verifiers. All four unchanged programs passed sixteen fresh replay conditions.
The task supplies a truthful receipt from one legal schedule, but no solver code.
Each agent acquired the actual constraints and constructed a recursive exploration
of all legal complete schedules, tracking separate saved registers and taking
the minimum terminal balance.

| Seed | Finite claim | Report / actual minimum | Queries | Result |
| --- | --- | --- | --- | --- |
| 21001 | False | -6 / -12 | 3 | Correct |
| 21002 | False | 5 / -1 | 3 | Correct |
| 21001 | True | -6 / -6 | 2 | Correct |
| 21002 | True | 5 / 5 | 3 | Correct |

Episode 001 initially referenced a nonexistent SQL column, then repaired that
error within the fixed budget. The other three first optimization queries were
correct. Episode 002 additionally returned a valid minimizing schedule among
336 complete schedules. All final explanations correctly distinguished a single
execution receipt from a proof of the minimum. Mean Brier loss was 0.000007;
there were no probability-direction contradictions or unsupported final claims.

The [frozen protocol](schedule-protocol-v1.md) uses two seed blocks, with identical
initial views across true/false cases. The source database's ordering constraints
are the distinguishing evidence. All queries run in the sandbox; the environment
models sequential consistency and is not a real operating-system concurrency test.
The sixteen fresh conditions per program vary signs, zeros, worker counts, IDs
and numeric bounds. These are program tests, not 64 extra model trials.

The result shows unscaffolded exact-verifier construction on these bounded tasks.
It does not establish a hard failure, broad concurrency competence, a treatment
effect, population accuracy or novelty. Removing a supplied solver did not create
the expected difficulty here. This is a different family from routes, so it does
not identify the causal effect of removing the scaffold.

Fifteen requests added $0.005803720 reported charges and $0.065646250 retained
reservations. Phase totals: **590 requests, $0.449982210 charges, $6.425077750
retained reservations**, against the unchanged $25 ceiling. No retries,
replacements, fallback routes or Daybreak rejections occurred in visible outputs.
The ledger, frozen-source and event audit passed; historical scope warnings remain.

Decision: decline an automatic larger peer comparison. The free next analysis
measures computational work inside a query: one credit can buy exhaustive search.
Four correct programs all use recursive UNION ALL, revisiting equivalent states.
Test a deterministic deduplication change separately, keeping all original agent
artifacts and their scores unchanged. Efficiency, semantic correctness and belief
are distinct outcomes. Novelty review has also found closer prior work on test
replay and evidence adequacy; a larger study requires a sharper contribution.
