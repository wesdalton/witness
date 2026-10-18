# Witness — Swarm Evidence Lab

An open research instrument for studying **when communication among AI agents
displaces independent verification**.

Run a swarm, trace a claim to its original evidence, compare policies under a fixed
effort budget, and export the experiment. The browser supports up to 10,000 simulated
agents. A separate Python harness collects real-model decisions through an optional
Inspect provider adapter.

**Research status:** the browser is an authored mechanistic model, not fitted LLM
behavior. Grounding fixtures, scripted harness runs, and an initial real-model pilot
are recorded. The pilot is an infrastructure check, not a test establishing the
proposed causal mechanism. The [pilot report](research/swarm/pilot-report.md) records
outcomes and failures; the [study protocol](research/swarm/protocol.md) distinguishes
implemented infrastructure from proposed experiments and maps the closest prior work.

[Open the public lab](https://witness-evaluation-lab.beigeglade34.chatgpt.site).

## Try it locally

Node 22+ and Python 3.12+; the website has no npm runtime dependencies or build step.

```bash
cd website
npm test
npm run serve
# Open http://localhost:4173
```

The page reads top to bottom as one argument: the grounded ledger case, the
communication-versus-checking tradeoff, an inspectable simulation, the recorded
real-model decisions, and the proposed study. In the simulation, six guided questions
each load a scenario and run all three evidence policies on the same agents and network.
Compare peak and time-averaged error as well as the final answer: two policies may both
recover while spending very different amounts of time mistaken. "Change the assumptions"
exposes the checking rule, reinforcement gain, ground truth, delay and seed.
The real-model section is built from the recorded pilot episodes by
`python scripts/build_site_data.py`.

Use **Export run** to download the trajectory and recorded interventions. Replay it:

```bash
node website/scripts/sweep.mjs --replay /path/to/witness-run.json
node website/scripts/sweep.mjs --seeds 10 --out /tmp/witness-sweep.json
```

A shared experiment link contains the configuration and restarts at round zero.
An export additionally preserves the executed trajectory and interventions. Browser
and CLI replay tolerate only very small belief/Brier floating-point differences;
discrete outcomes and evidence identity must match.

## Run the decision harness

No provider is invoked by default. This standard-library command uses a scripted
policy and recorded observations:

```bash
python -m swarm_lab.experiment --out /tmp/witness-smoke.json
```

For live model experiments, install the optional provider tooling used by this
repository and configure its provider credential in your environment. Choose the
model explicitly; do not place keys in the website or output files.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
python -m swarm_lab.experiment \
  --model provider/model-id \
  --population 8 --rounds 8 --max-calls 64 --max-output-tokens 256 \
  --fixture honest_fix --treatment ancestry --out /tmp/witness-model.json
```

`provider/model-id` is a placeholder, not a default model recommendation. The CLI
rejects planned decisions above the call ceiling before invoking a provider. Provider
retries are disabled. A call limit is not a dollar limit: provider input, output and
reasoning-token pricing still apply. Usage returned by the provider is logged.

Repeat with `pytest_module_shadow` to obtain the matched false-claim fixture. Its
initial report is identical to the honest fixture's report; the independent probe
differs. Treatments are `reports`, `ancestry`, and `reserved`. The last charges every
agent for one forced first-turn check. It is a simple harness baseline, distinct from
the browser's per-round allocation rule. Full factorial experiments, causal branching
and fitted dynamics are proposed work, not features claimed by this release.

Invalid outputs fail closed to abstention, remain in the event log, and contribute
to failure counts. `--parse-mode lenient` instead accepts a leading JSON object and
flags each such output as a format violation; strict parsing is the default. Each run writes an append-only JSONL record and final JSON result;
existing outputs are not overwritten. Model-facing evidence excludes the observer's
truth and fixture identity. Inspect supplies a provider adapter, not the research
model or a requirement for the website.

### Run a cost-bounded OpenRouter pilot

`swarm_lab.pilot` adds persistent dollar reservations, a provider-side key-limit
check, pinned routing, model-specific billing contracts, and optional request pacing.
It defaults to planning only. Put a dedicated `OPENROUTER_API_KEY` in your local
environment or `.env`; the public browser never receives it.

```bash
python -m swarm_lab.pilot \
  --model openrouter/openai/gpt-6-luna --provider openai \
  --input-price 0.1 --output-price 0.5 --price-as-of 2026-10-18 \
  --billing-reference https://openrouter.ai/openai/gpt-6-luna \
  --population 4 --rounds 4 --fixture pytest_module_shadow \
  --treatment reports --max-calls 16 --min-request-interval 3.2 \
  --out research/swarm/my-calibration
```

The example is a dry run. Verify current pricing and the billing contract before
adding `--billing-bounds-confirmed --live`. The project authorization ceiling is
US$100 across the persistent ledger, with a US$5 default batch ceiling; these are
upper bounds, not spending targets. Reservations are retained after errors. Do not
delete the ledger to reset spending. No provider retries or fallback routes are used.
See the [initial pilot plan](research/swarm/pilot-plan.md).

Summarize finished episode JSON files with `python -m swarm_lab.analyze RUN.json
--out SUMMARY.json`. Infrastructure-failed episodes are marked ineligible for
behavioral comparisons. Agents within an episode are not independent replicates.

## What is in the release?

| Component | Purpose |
|---|---|
| `website/dist/` | Browser interface and shared mechanistic engine |
| `website/tests/`, `website/scripts/` | Engine invariants, replay and parameter sweep |
| `swarm_lab/` | Bounded synchronous agent-decision environment and provider interface |
| `research/pilots/` | Four authored scorer-integrity fixtures and recorded subprocess evidence |
| `research/swarm/` | Methods, protocol, prior art, synthetic artifacts and recorded live pilots |
| `inspect_tasks/`, `sandbox/` | Original Inspect evaluation baseline and ledger task |

The [methods](research/swarm/methods.md) specify the update equations, cost accounting,
source assumptions and limitations. The [design notes](research/swarm/design.md)
explain how established safety tooling informed evidence inspection and run identity.
The original Inspect work sample is documented in
[the preserved README](research/legacy-inspect-readme.md).

## Validate and contribute

```bash
node --test website/tests/*.test.mjs
python -m pytest -q
ruff check .
python -m research.pilots.scorer_integrity --output /tmp/witness-grounding.json
```

Useful contributions include new matched true/false case families, independent
observation processes, asynchronous scheduling, noisy/forged evidence experiments,
and held-out model comparisons. Changes to dynamics need versioned exports and
reproduction checks. Keep synthetic, scripted and real-model evidence separately
labeled; never relabel smoke runs as empirical findings.

The canonical website source lives in `website/`. Hosting uses a separate checkout
containing that source; its manifest and deployment credentials are not part of the
research artifact. `python scripts/package_witness.py` produces an explicit, bounded
source archive for the website without local credentials, Git history or caches.

Code and original project documentation are MIT licensed. Linked papers retain their
respective rights. Cite the software using `CITATION.cff`; citing
this prototype does not imply that its proposed scientific claims have been tested.
