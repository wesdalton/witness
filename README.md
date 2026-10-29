# Witness

A research prototype on how AI auditors verify claims about agent runs, and what
evidence they need to do it. **No behavioral finding is established yet.** The
current state of every study is in [research/findings.md](research/findings.md).

## Where things stand

- **Active question:** the evidence-access benchmark ([research/directions.md](research/directions.md),
  Option 1). It uses paired valid and invalid runs that look identical under
  restricted access, and asks which added evidence lets an auditor tell them apart.
  The 48-incident corpus is built and has passed every free gate; no model has
  been run on it yet. Code: `swarm_lab/evidence_access/`.
- **Closed studies:** the swarm pilot, single-claim auditor, portfolio allocation
  screen, and query capability series. They hit ceilings or were underpowered.
  Their runners are kept under `swarm_lab/legacy/` and refuse paid runs.
- **Validated results:** a capable auditor exposed two wrong labels in our own
  benchmark, and replayed probe output can differ for incidental reasons such as
  memory addresses. Both are measurement findings, not agent behavior.
- **Budget:** $25 phase ceiling. 590 requests, $0.449982210 billed
  (`research/agent-study/budget.jsonl`).

Operating rules for research work are in [AGENTS.md](AGENTS.md).

## Layout

| Path | Contents |
| --- | --- |
| `swarm_lab/core/` | Phase budget, OpenRouter client, Docker sandbox, records, evidence archive |
| `swarm_lab/evidence_access/` | Active benchmark: tasks, corpus builder, baselines, Stage 1 runner |
| `swarm_lab/legacy/` | Closed study runners and case builders (historical reproduction) |
| `scripts/` | Evidence audits, archive CLI, site build; `scripts/legacy/` for closed studies |
| `research/findings.md` | One current report covering every study |
| `research/registry/` | Write-once SHA-256 records of all sealed evidence, plus derived index |
| `research/archive/` | Sealed writeup editions and the content-addressed snapshot store |
| `inspect_tasks/`, `website/` | The original Inspect tasks and browser prototype |

## Validate the repository

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/python scripts/research_archive.py audit
.venv/bin/python scripts/audit_research_coverage.py
.venv/bin/python scripts/audit_agent_study.py
```

Run source snapshots are stored once per distinct file. To rebuild the original
snapshot folders somewhere for inspection:

```sh
.venv/bin/python scripts/research_archive.py restore --to /tmp/witness-snapshots
```

## Run the browser prototype

The website has no runtime dependencies or build step. With Node 22+:

```sh
cd website
npm test
npm run serve   # http://localhost:4173
```

It runs an authored 10,000-agent simulation from the 18 October stage, not the
later live-model studies. [Published prototype](https://wesdalton.github.io/witness/).
The [original Inspect documentation](research/legacy-inspect-readme.md) covers
the earliest tasks.

Code and original documentation are MIT licensed; vendored libraries keep their
licenses. Cite with `CITATION.cff`.
