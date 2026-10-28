# Archived-probe repeatability negative controls

Exploratory measurement audit, frozen before new local replays. Initial inspection
found object addresses in three of 76 existing archived probes. Include ALL 76,
not only the suspicious examples. No new LLM inference, downloads or API spending.
This is independent work on existing evidence; the blocked repository-corpus
setup remains stopped.

Question: can the raw tuple (exit code, stdout, stderr) differ when exactly the
same agent-written probe runs on exactly the same implementation? If so, an
unqualified between-implementation text difference cannot count as fault detection.
The historical replay tool already calls these observations candidates requiring
semantic review. This audit tests that warning; it does not change original scores.

Population: every probe in research/portfolio/*/probe-replay*.json at freeze time.
Deduplicate by (family, code SHA-256), retaining ALL origins. Snapshot the selection,
source and input hashes. For each probe and each archived implementation variant,
execute twice in fresh isolated containers with the original pinned image. Require
current workspace source hashes to match the archived hashes before executing.
Stop on mismatched provenance. Keep raw outputs and failed/timed-out executions.

Primary endpoint: unequal raw signatures across the two identical-source repeats.
Secondary: archived raw between-variant differences erased solely by replacing
Python object/function repr addresses with a placeholder. This deliberately narrow
normalization must not erase ordinary hexadecimal payloads or numeric results.
Report timeouts and truncated output separately; do not count them as comparisons.
No repeatability claim extends beyond two repetitions. Finite source-consistency
controls do not establish a correct oracle; source dumps and API misuse still need
manual review. Report all suspect probes with code and provenance.

Decision: if negative controls trigger, future paid peer tests require a semantic
outcome extractor or assertion oracle plus repeated same-source controls. Otherwise
retain the current conservative semantic-review rule. This is a measurement finding
within Witness, not proof of a social effect or research novelty. Test replay and
oracle-quality measurement overlap https://arxiv.org/html/2607.28871 and
https://arxiv.org/html/2610.32548.
