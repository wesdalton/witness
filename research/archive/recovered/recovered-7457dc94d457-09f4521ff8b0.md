# Witness research records

Start with [findings.md](findings.md): one current report for every study, with
links to raw runs and archived detail. The [experiment index](registry/index.md)
lists every sealed bundle.

## Layout

```
findings.md               current report across all studies
directions.md             background for the active evidence-access question
experiments/<id>/         new studies (one directory per experiment)
  design/                 frozen question, protocol, power analysis
  gates/<gate-id>/        offline validation and corpus provenance
  runs/<run-id>/          manifest, source snapshot, raw traces, completion
  analyses/<id>/          derived results linked to input bundles
  reports/<edition>/      versioned narrative
  adjudications/<id>/     corrections; never rewrite the original evidence
agent-study/ portfolio/ swarm/
                          closed studies: raw runs, frozen protocols, JSON artifacts
registry/bundles/         write-once SHA-256 inventories of sealed evidence
registry/packs/           write-once maps from packed paths to stored objects
archive/legacy-writeups/  sealed editions of retired narrative writeups
archive/objects/          content-addressed store for run source snapshots
```

## Rules

Create designs and bundles with `swarm_lab.core.archive.Archive`. Files are written
once; existing IDs and paths are rejected. Seal a bundle when it is complete and
link its parents. Aborted runs are sealed as aborted, never reused. Never put a
correction inside a sealed run; write an adjudication instead. Do not rebaseline a
checksum mismatch.

The phase ledger is `agent-study/budget.jsonl`. It is append-only and locked.
Exposure counts settled requests at billed cost and anything else at its full
reservation.

Run source snapshots are packed into `archive/objects/` after sealing, one copy
per distinct file. The audit verifies packed files through the store.
`scripts/research_archive.py restore --to DIR` rebuilds them byte for byte. The
packing record for 29 October was verified this way against git: all 1,036 files
matched.

Retired writeups were removed from the study folders only when a byte-identical
sealed edition already existed in `archive/`. Older documents may still link to
their retired paths; [findings.md](findings.md) links the sealed editions.

## Checks

```sh
.venv/bin/python scripts/research_archive.py audit
.venv/bin/python scripts/audit_research_coverage.py
.venv/bin/python scripts/audit_agent_study.py
```

`audit_research_coverage.py` also scans the ignored `logs/` directory. Use
`--capture-legacy` to archive a new edition of a root `research/*.md` file after
editing it. Integrity checks guard against overwrites; they are not tamper-proof
storage or an off-machine backup.
