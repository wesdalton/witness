# Held-out task development — no model inference yet

Prepared while the fixed allocation screen runs. Do not choose or tune this task
based on interim treatment outcomes. No agent has been evaluated on it yet.

The new family is inventory reconciliation from a real SQLite database containing
orders, order-status revisions, and movement revisions. It is an authored
generated-data task, not a historical upstream software bug. Agents must compute
the correct aggregate under explicit as-of, effective-time, latest-revision,
warehouse, status, shipment, and return rules.

This addresses a limitation exposed by v1: a narrow reference suite was treated
as proof of a broad software claim. Here the claim concerns one finite database
and one exact integer aggregate. Independently implemented Python iteration and
SQL window queries must agree before any candidate is usable. Paired true/false
worlds have the same disputed report; one guaranteed included movement changes
by a nonzero signed amount in the false world. Both databases remain valid.
Reference totals and generating code never enter the agent workspace.

The public smoke test checks only database integrity. A passing result cannot
establish the aggregate. Model-generated SQL/Python can interrogate the live
database. Complex revision ordering makes summing raw rows, filtering before
selecting the latest revision, or counting future updates incorrect.

This is a development artifact. A held-out experiment still requires a frozen
protocol, a free reference gate, model capability calibration, and a decision
based on the completed exploratory screen. It will be reported as an authored
domain transfer, with no claim of broad real-world validation.

## Free measurement improvement during development

The first generator distinguished 13 of 14 authored incorrect SQL queries across
20 worlds. It failed to distinguish choosing the latest arrival timestamp from
choosing the highest revision, because these orders always coincided. It also
never generated an order with no known status. Agreement between two correct
oracles would not expose this missing challenge.

Generator revision 2 adds explicit out-of-order arrivals, a movement-kind change,
and an order without known status. The original generator remains reproducible
via revision=1. All 15 audited incorrect queries (including a new missing-status
variant) now disagree with the reference in all 20 tested worlds. These are
authored mutation checks, not agent outcomes or exhaustive correctness proof.
No paid inference preceded this repair. Keep both development audit artifacts.
