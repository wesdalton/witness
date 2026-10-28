# Evidence completeness audit — 28 October 2026

The first registry pass covered the 25 historical run directories with manifests,
their raw traces, source snapshots, analyses and writeup editions. It did not
include the Git-ignored `logs/` tree or two root-level historical writeups. The
follow-up completeness check scans both `research/` and `logs/` and makes these
omissions visible instead of assuming that existing registry records are complete.

Recovered evidence comprises nine September Inspect `.eval` files (three initial
checks and six sandbox scenarios), one October analysis smoke file, the historical
root writeups, and snapshots of both spending ledgers. Exact bytes are retained
under `research/archive/recovered/`; originals remain at their previous paths.
The index links both. Every recovered Inspect file identifies `mockllm/model`.
They contain eleven saved samples in total and are scripted infrastructure checks,
not additional real-model experiments. The compressed logs were decoded with the
installed Inspect log reader, without any inference requests.

Historical qualification: `legacy-inspect-readme.md` reports four scored reasoning
samples with mean 0.675, but the available `adversarial-reasoning` log contains
three saved samples, all with NaN scores. That file does not substantiate the
README's numerical claim. A different run might once have existed; we have not
reconstructed one. Preserve the report and the available raw evidence separately.

The 19 later live-auditor batch manifests contain 128 attempted episodes: 124
completed and four incomplete. The six October 18 swarm manifests use a separate
recorded-observation protocol and ledger. Local replay executions are not extra
independent agent trials. The October 24 phase's 590 requests reconcile with its
traces and ledger; the early interrupted calibration still lacks a full source
snapshot. Invalid v1 labels and later contract limitations remain separately
adjudicated. Archive registration does not repair those historical limitations.

“All recorded” means all experiment evidence currently found in this repository's
`research/` and `logs/` trees is retained and accounted for by the completeness
check. It does not prove that no experiment was ever unrecorded, recover deleted
history, or provide an off-machine backup. Source code, fixtures and website
exports remain under their ordinary Git paths. The website copy is a derived
presentation, not a second independent experiment.

The new completeness check also compares live ledgers with every archived prefix.
Appending new requests is allowed; deleting or replacing old entries is flagged.
Living writeups require a new archived edition when their content changes. The
separate SHA-256 bundle audit detects edits, additions and deletions within sealed
evidence. Both checks are required before and after future research work.
