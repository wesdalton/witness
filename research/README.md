# Witness research records

Start at the [experiment index](registry/index.md). It links frozen designs,
raw runs, analyses, report editions, and corrections. Legacy evidence remains at
its original paths; the index also links archived editions of the older writeups
and their living originals (whose relative links remain navigable).

New experiments use this layout:

```
experiments/<experiment-id>/
  design/                  # frozen question, protocol and decision criteria
  gates/<gate-id>/          # offline validation and corpus provenance
  runs/<run-id>/            # manifest, source snapshot, raw traces, completion
  analyses/<analysis-id>/   # derived results, links to exact input bundles
  reports/<edition-id>/     # separately versioned narrative
  adjudications/<id>/       # corrections; never rewrite the original evidence
```

Create designs and bundles with `swarm_lab.research_archive.Archive`. File writes
use `write_once`; existing IDs, output paths and files are rejected. Seal a bundle
when complete, linking its parent bundle IDs. Never add a correction inside a
sealed run. Aborted runs remain evidence and must be sealed as aborted, not reused.
Each runner freezes exact source, prompt, configuration and corpus hashes before
inference. The shared phase ledger stays at `agent-study/budget.jsonl`; it is
append-only, locked, and retains every reservation including failures.

`registry/bundles/*.json` holds write-once SHA-256 inventories. The audit detects
file edits, additions and deletions. `registry/index.md` and `index.json` are
replaceable indexes derived from those records, never the authoritative results.
Git records the inventories and evidence. These are overwrite guards and integrity
checks, not tamperproof storage or an off-machine backup. Legacy seals establish
the baseline on registration, not historical proof of immutability. Legacy live
overviews may still change; their archived editions remain unchanged.

Run before and after research work:

```sh
.venv/bin/python scripts/research_archive.py audit
.venv/bin/python scripts/audit_research_coverage.py
.venv/bin/python scripts/audit_agent_study.py
```

Regenerate navigation with `scripts/research_archive.py index`. Use `bootstrap`
only to register legacy runs and archive new editions of legacy writeups/analyses.
Do not rebaseline a changed sealed bundle: investigate and write an adjudication.

The completeness check additionally scans `logs/`, including Git-ignored early
Inspect files. Historical logs are copied into `research/archive/recovered/` and
indexed with their original location. Preserve mock/scripted labels: these logs
do not become live-model evidence merely because they use the Inspect format.
`scripts/audit_research_coverage.py --capture-legacy` archives previously omitted
root writeups, ignored logs and ledger snapshots. It detects unregistered evidence,
changed writeup editions, and changes to archived ledger prefixes while permitting
new ledger entries. Completeness means all evidence currently found in these
directories; it cannot recover missing historical files or unrecorded work.
