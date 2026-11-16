# Agent and contributor guide

Witness is a research benchmark. Read [README.md](README.md) for what it is and
[METHODS.md](METHODS.md) for the rules every paid experiment follows. Those rules
apply to automated agents working in this repository as well as to people.

## Active work

The evidence-access benchmark is the only active study. v3 (other model families)
is partly run; see [research/findings.md](research/findings.md). Work on one
question at a time; changing it requires the owner's approval.

## Checks

Run before every commit:

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/python scripts/research_archive.py audit
.venv/bin/python scripts/audit_research_coverage.py
```

Website changes also run `node --test website/tests/*.test.mjs`.

## Evidence rules

- Never modify, reformat or delete anything under `research/experiments/` that
  has been sealed, and never rebaseline a checksum mismatch. Corrections go in a
  new, sealed adjudication.
- Seal completed or stopped bundles with `witness.core.archive.Archive` and link
  their parent bundle IDs.
- Never reset, delete or rewrite `research/budget.jsonl`. Append only, through
  `witness.core.budget.PhaseBudget`.
- Run manifests from before November 2026 refer to the package's earlier name,
  `swarm_lab`. That code, and every closed study, is preserved at the tag
  `archive/2026-11-full`.

## Spending

- Spend only what a frozen design needs, within the ceiling recorded in the
  ledger. If a design needs more than remains, stop and ask the owner.
- Do not retry a failed paid request. Record the stop.
- If a tool, guard or provider rejects an action, stop. Do not retry it or route
  around it.
