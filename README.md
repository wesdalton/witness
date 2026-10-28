# Witness — Swarm Evidence Lab

A research prototype for studying whether communication among AI agents changes
independent verification. **No novel behavioral finding is established.** Current
work is question selection and interpretation of existing evidence; no next paid
batch is selected.

[Experiment index](research/registry/index.md) ·
[Storage and correction rules](research/README.md) ·
[Evidence completeness](research/archive-completeness-20261028.md) ·
[Literature comparison](research/portfolio/novelty-review.md)

## Evidence so far

- A capable auditor exposed two incorrect benchmark labels. Those raw results
  remain preserved with [separate adjudication](research/portfolio/report.md).
- The [allocation screen](research/portfolio/allocation-screen-report.md) is
  inconclusive. Later SQL capability tasks repeatedly reached ceilings and are
  closed to routine expansion.
- The [probe repeatability audit](research/experiments/20261028-probe-repeatability-v1/reports/edition-01/report.md)
  found incidental output differences and improved measurement. This is a local
  validity result, not a new general phenomenon about agents.
- The browser is an authored simulation. September Inspect logs are scripted
  checks; October 18 agents retrieved recorded observations. Later live-tool
  audits and local replays are separately labeled in the index.

The active research phase has a **$25 total ceiling**, including previous work.
Its append-only ledger is `research/agent-study/budget.jsonl`. At this revision it
records 590 requests, $0.449982210 reported charges and $6.425077750 retained
reservations. The older October 18 ledger remains separate. Neither is reset.

## Maintenance scope

| Area | Status |
| --- | --- |
| Evidence, source snapshots, writeups and corrections | Preserve; check integrity and completeness |
| Budget ledger, API adapter, isolated execution | Shared primitives; change for a demonstrated need |
| Ledger, portfolio, inventory, route and schedule runners | Historical reproduction; no new batch selected |
| Website and original Inspect tasks | Earlier prototype, independently runnable |

New experiment code requires a specific unresolved prediction, a comparison with
the closest prior experiment, and a result that would change a research decision.
Use existing tools for the smallest discriminating test. A new general framework
or another easy capability task is not a research objective.

The unvalidated `repo_cases.py` draft was removed from the active package. It
produced no experiment records and had no callers. Its exact source remains in
Git at `3f92abf:swarm_lab/repo_cases.py`; the [historical setup stop](research/repository-audit-status-20261028.md)
is preserved. Removing the draft does not authorize retrying that blocked setup.

## Validate the repository

With the existing development environment:

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/python scripts/research_archive.py audit
.venv/bin/python scripts/audit_research_coverage.py
.venv/bin/python scripts/audit_agent_study.py
```

Frozen historical source is evidence; do not rewrite it to satisfy current lint.
New runs and writeup editions use unique paths and refuse overwrites.

## Run the browser prototype

The website has no npm runtime dependencies or build step. Using Node 22+:

```sh
cd website
npm test
npm run serve
# Open http://localhost:4173
```

The browser supports exporting and replaying simulated trajectories. Its public
presentation describes an earlier research stage; the experiment index contains
the later work. [Open the published prototype](https://wesdalton.github.io/witness/).

Historical runner configurations and exact source are recorded with each run.
The [original Inspect documentation](research/legacy-inspect-readme.md) is retained
with its known [documentation/log discrepancy](research/archive-completeness-20261028.md).

Code and original documentation are MIT licensed; vendored libraries retain their
licenses. Cite the software using `CITATION.cff`. Software availability does not
establish its proposed scientific claims.
