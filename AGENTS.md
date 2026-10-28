# Witness research operating instructions

The user delegated research direction and execution on 24 October 2026 and asked
for an iterative research loop toward interesting, validated, novel findings.
They authorized **$25 total for the phase**, including pilots and replications,
and asked that each stage justify the next dollar. They subsequently raised
concerns about novelty and technical debt. Continue research through focused
question selection, evidence review and the smallest justified experiments.

## Research scope

No next paid batch is selected. The completed studies are historical reproduction
tools, not an active backlog of frameworks to extend. Before adding experiment
code, identify the unresolved prediction, the closest existing experiment, the
specific difference, and what each possible outcome would change. Prefer existing
tools. Do not build another general runner or keep raising task difficulty merely
to produce model errors. Infrastructure improvements alone are not novel findings.

Read `README.md`, `research/README.md`, and the registry index. Use
`research/portfolio/novelty-review.md` and `loop-decisions.md` for prior decisions.
Before continuing a particular study, read its frozen protocol, report and
adjudications. Original decisions remain in `research/agent-study/decisions.md`
and `research/portfolio/decisions.md`; old proposed designs are not completed work.

## Preserved scientific restrictions

- Portfolio v1 is disabled: the stronger calibration exposed two invalid positive
  labels. Preserve its raw results and exclude invalid accuracy/Brier scores.
  V2 uses separately repaired contracts; it does not erase v1's failures.
- The original ledger, inventory, inherited-query, route and schedule capability
  tasks reached ceilings. Do not repeat or expand them without a new scientific
  justification. The allocation screen is inconclusive, not equivalence. Its three
  incomplete episodes and probability/interpretation problems remain in the record.
- SQL call count is not computational effort. Finite replay success does not prove
  universal correctness; preserve numeric-contract adjudications separately.
- Different replay text and zero exit status do not establish semantic fault
  detection. Prospective replay v2 adds same-source repeats and diagnostic address
  normalization. Even repeatable differences require a valid behavioral oracle.
- Keep simulations, scripted Inspect checks, recorded-observation agents, live
  tool-using agents and local replays distinct. Historical peer messages were
  authored stimuli, not an independently executing swarm. Repeated probes or cases
  are not independent projects. Null or beneficial effects are valid outcomes.

## Execution and spending

Before each paid batch, freeze its question, decision value, source/prompt/config,
maximum reservation and stopping criteria. Review validity, confounds, floor or
ceiling effects, and cheaper ways to resolve the uncertainty. Do not pool changed
configurations or score infrastructure failures as model mistakes. Authorization
within the existing scope does not require asking the user for the same approval.

Use `research/agent-study/budget.jsonl` for the current $25 phase. Keep all previous
reservations and failed attempts. Never reset, delete or silently replace a ledger.
October 18's separate ledger also remains intact. Report provider charges separately
from retained reservations. The current ledger, not a historical report, is authoritative.

The user instructed us to stop actions blocked by Daybreak. Treat rejections as
stops without retries or alternate routes. A combined three-library setup command
was rejected before execution on 28 October; see
`research/repository-audit-status-20261028.md`. That setup remains stopped.
Its unused draft builder was removed from the active package and is preserved at
`3f92abf:swarm_lab/repo_cases.py`. No corpus or inference run resulted from it.

## Evidence and validation

Use unique experiment/run IDs and write-once output files. Seal completed or
aborted bundles with `swarm_lab.research_archive.Archive`; link parent IDs. Keep
analyses, report editions and corrections separate. Never modify sealed evidence
or rebaseline a checksum mismatch. Derived registry indexes are replaceable.
The completeness check covers `research/` and ignored `logs/`. Preserve historical
gaps, including the early missing source snapshot and README/log discrepancy.

Required checks: `.venv/bin/python -m pytest -q`, `.venv/bin/ruff check .`,
`.venv/bin/python scripts/research_archive.py audit`,
`.venv/bin/python scripts/audit_research_coverage.py`, and
`.venv/bin/python scripts/audit_agent_study.py`.
Browser changes additionally use `node --test website/tests/*.test.mjs`.
Frozen source snapshots are historical evidence; do not reformat them for lint.
