# Witness research operating instructions

The user delegated research direction and execution on 24 October 2026 and wants
interesting, validated, novel findings. On 29 October 2026 the user approved an
external audit and its fixes. That audit concluded that the earlier
loops had excellent provenance but produced no finding. The causes were weak
treatments, underpowered comparisons, and tasks at a capability ceiling. These
rules exist to prevent a repeat.

## Active question

**Evidence-access benchmark** (Option 1 in `research/directions.md`). For paired
incidents where a valid and an invalid run produce identical observations under a
restricted access policy, which additional evidence (full artifacts, independent
run manifest, auditor-controlled replay) lets an auditor resolve the claim, and do
LLM auditors correctly ask for that evidence instead of guessing?

Work on one question at a time. Changing the active question requires the user's
approval. Earlier studies (swarm pilot, ledger, portfolio allocation, query, route,
schedule, output-requirement) are closed. Their code is historical reproduction
code under `swarm_lab/legacy/`, not a backlog.

## Design rules for any comparison that costs money

1. **Freeze before dispatch:** question, primary endpoint, minimum effect worth
   detecting, sample size, exclusions, analysis, stopping rule, and maximum spend.
2. **Power first.** Compute the sample size needed to detect the minimum effect at
   the frozen alpha. Do not run a comparison that cannot detect that effect. A
   small pilot to estimate variance or discordance is allowed if labeled as such.
3. **Calibrate difficulty before comparing treatments.** On development instances
   with a no-treatment arm, adjust tasks until the baseline primary outcome sits
   roughly between 30% and 70%. Tuning difficulty this way is standard practice,
   not manufacturing errors. Never tune using treatment-arm outcomes, and never
   reuse development instances for the test set.
4. **Use a real treatment dose.** Stimuli must be plausible and strong enough to
   matter. Include dose levels (none / weak / strong) when the question allows.
   Avoid prompts that explicitly prime the model against the manipulation unless
   that priming is itself a varied factor.
5. **Ground truth is executable.** Labels come from at least two independent
   reference implementations or exhaustive checks, plus mutation tests. An LLM's
   opinion is never the only ground truth. Paired cases must not leak the label
   through names, hashes, sizes, wording or ordering.
6. **Count units honestly.** The unit of analysis is the independent incident or
   seed. Repeated probes, turns or claims from one source family are not
   independent. Report uncertainty clustered by family, and test a held-out family.
7. **Report every outcome plainly.** Nulls and beneficial effects are valid
   results. Keep simulations, scripted checks, recorded-observation agents, live
   agents and local replays distinct.

## Spending

The phase ceiling is **$25**, recorded in `research/agent-study/budget.jsonl`.
Spend what a frozen design needs. If a design needs more than the remaining
ceiling, stop and ask the user. Exposure counts provider-reported cost for settled
requests and the full reservation for anything outstanding, failed or unpriced
(`swarm_lab.core.budget.exposure`). Never reset, delete or rewrite a ledger.
October 18's separate ledger also stays intact.

The user instructed us to stop actions blocked by Daybreak. Treat a rejection as a
stop: no retries, no alternate routes. The 28 October three-library setup stop is
recorded in `research/repository-audit-status-20261028.md`.

## Evidence

- Use unique run IDs and write-once outputs. Seal completed or aborted bundles
  with `swarm_lab.core.archive.Archive` and link parent IDs.
- Never modify sealed evidence or rebaseline a checksum mismatch. Corrections go
  in a separate adjudication.
- Run source snapshots are packed into `research/archive/objects/` (one copy per
  distinct file). Read them with `Archive.read_bytes`, or rebuild the original
  folders with `scripts/research_archive.py restore --to DIR`.
- Each experiment has one current report. Put limitations in one section of that
  report instead of repeating caveats in every paragraph. Superseded writeups move
  to `research/archive/`; nothing is deleted.
- Restricted earlier results stay restricted: portfolio v1 accuracy/Brier is
  excluded (two invalid labels); the allocation screen is inconclusive, not
  equivalence; replay text differences are not fault detection without an oracle.

## Required checks

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/python scripts/research_archive.py audit
.venv/bin/python scripts/audit_research_coverage.py
.venv/bin/python scripts/audit_agent_study.py
```

Browser changes additionally run `node --test website/tests/*.test.mjs`. Frozen
source snapshots are historical evidence; do not reformat them for lint.
