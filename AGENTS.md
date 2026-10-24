# Research operating instructions

The user delegated Witness research direction and execution on 24 October 2026.
They authorized **$25 total for this research phase**, including the pilot and
follow-up replications, and explicitly asked for assessment and improvements at
every stage so that future dollars are spent well.

Read `research/agent-study/report.md`, `decisions.md`, and `next-experiment.md`
before continuing research. The next-experiment document is a design draft,
not an implemented or completed study.

Also read `research/portfolio/report.md` and `decisions.md`: the portfolio
successor is implemented, but live inference is now stopped by a validity guard.
One GPT-6.1 Sol calibration found reproducible counterexamples in two candidates
labeled correct. Do not interpret its original accuracy/Brier as model errors or
run more v1 portfolios. Preserve the raw labels and separate adjudication. A new
protocol and a stronger reference gate are required before further paid inference.

The user additionally instructed: stop doing things that Daybreak blocks. Treat
rejections as stops; do not retry blocked actions through another route or tool.

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

Current evidence: all 16 ledger screening episodes acquired source evidence and
answered correctly, regardless of peer-message arm. Stop repeating that setup.
The next useful study needs an actual opportunity cost across competing claims.
Null or beneficial effects are valid results; do not tune cases to manufacture harm.

Latest phase accounting: 85 requests, $0.089660865 response-reported cost and
$1.217083625 retained reservations. This includes the seven-request portfolio
calibration ($0.079943), alongside the prior 78 requests. Do not reset the ledger.

Validation: `.venv/bin/python -m pytest -q`, `.venv/bin/ruff check .`, and
`.venv/bin/python scripts/audit_agent_study.py`. Browser changes additionally use
`node --test website/tests/*.test.mjs`. Frozen source snapshots under each batch
are historical evidence; do not reformat or edit them to satisfy current lint.
