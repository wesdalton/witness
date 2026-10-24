# Research operating instructions

The user delegated Witness research direction and execution on 24 October 2026.
They authorized **$25 total for this research phase**, including the pilot and
follow-up replications, and explicitly asked for assessment and improvements at
every stage so that future dollars are spent well.

Read `research/agent-study/report.md`, `decisions.md`, and `next-experiment.md`
before continuing research. The next-experiment document is a design draft,
not an implemented or completed study.

Also read `research/portfolio/report.md`, `decisions.md`, and `loop-report.md`:
the original portfolio version is stopped by a validity guard.
One GPT-6.1 Sol calibration found reproducible counterexamples in two candidates
labeled correct. Do not interpret its original accuracy/Brier as model errors or
run more v1 portfolios. Preserve the raw labels and separate adjudication. A new
protocol and a stronger reference gate are required before further paid inference.

The user additionally instructed: stop doing things that Daybreak blocks. Treat
rejections as stops; do not retry blocked actions through another route or tool.

The user subsequently explicitly requested a continuous research LOOP toward
interesting, validated, novel findings. Use research/portfolio/loop-decisions.md
and novelty-review.md. Continue review, hypothesis revision, implementation, and
the next justified experiment without repeatedly stopping at a plan. Do not
guarantee novelty or conclusive results; establish them with literature comparison,
valid references, a frozen confirmatory design, and independent replication.
V1 stays disabled. V2 uses separate repaired contracts and an expanded mandatory
reference gate; its implementation does not erase v1's failures.

Before each paid batch, record the question, why its answer would change a
research decision, a maximum reservation, and stopping criteria. Review the
preceding stage's validity, failure modes, floor/ceiling effects, alternative
explanations, and cheaper ways to resolve the uncertainty. Do not spend the
allocation just because it is available. Calls within the existing authorization
do not require asking the user for the same approval again.

Use the persistent `research/agent-study/budget.jsonl` ledger for this phase.
Retain previous reservations and all failed attempts. Never reset, delete, or
silently replace the ledger to obtain a new budget. October 18's separate ledger
and pilot records must also remain intact. Costs and conservative reservations
must be reported separately.

Keep simulated behavior, scripted smoke checks, model decisions that retrieve
recorded observations, and live tool-using agents distinct. The October 24
completed cohorts contain 24 live-tool audit episodes; four include model-written
Python/SQL. Peer messages in the ledger screen were authored stimuli. This is
not yet a study of an independently running multi-agent swarm.

Freeze source/prompt/protocol configurations before inference, preserve raw
outputs, and version changes. Do not pool changed configurations or classify
infrastructure failures as model mistakes. A tool invocation does not itself
prove adequate verification; inspect the code, output, and claim. Correct source
reasoning can count as evidence without execution.

Current evidence: all 16 original ledger screening episodes acquired source
evidence and answered correctly; stop repeating that setup. Repaired portfolio
v2 passed capable-model calibration. Luna/medium with navigation hints also
passed the two-credit capability gate; Luna without reasoning did not. The fixed
32-episode allocation screen is complete: 29 completed, three incomplete, no
retries/replacements. Its allocation contrast is inconclusive; see
allocation-screen-report.md and screening-01-continuation.md. Four no-peer
executable-query audits passed all fresh-data replay conditions, but every first
aggregate query was correct: do not scale that likely ceiling. The next frozen
capability pilot tested inherited correct/flawed queries and truthful execution
receipts: all eight passed, including fresh program replay. It is not being scaled.
A separate joint route-optimization capability pilot also passed all eight episodes
and thirty replay conditions per program. Read route-calibration-report.md.
The next frozen screen tests mandatory-program versus verdict-only output, crossed
with neutral/endorsement messages. Its same_program route mode removes the earlier
code/label cue: identical initial evidence, different finite database truth. Read
output-requirement-protocol-v1.md and loop-decisions.md before further spending.
New routes are authored finite tasks, not independent real projects.
Null or beneficial effects are valid results; do not tune cases to manufacture harm.

Accounting before output-requirement screening: 435 requests, $0.407355740 reported
cost and $5.810092000 retained reservations. Later batches add to this;
read the current ledger before spending. Do not reset the ledger.

Validation: `.venv/bin/python -m pytest -q`, `.venv/bin/ruff check .`, and
`.venv/bin/python scripts/audit_agent_study.py`. Browser changes additionally use
`node --test website/tests/*.test.mjs`. Frozen source snapshots under each batch
are historical evidence; do not reformat or edit them to satisfy current lint.
