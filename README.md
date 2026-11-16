# Witness

**Do LLM auditors know when the evidence cannot settle a claim about an agent run?**

Witness is a controlled benchmark that tests whether an AI auditor can tell when
the evidence it has been given cannot verify an agent's claim, and whether it
uses the evidence that can.

The main result so far is about exit codes. On held-out tasks, GPT-6 Luna and
GPT-6.1 Sol accepted a test run as passing in every case where the replay showed
exit status 0, no output and no test summary. Real pytest always prints a summary,
so that record shows that no tests ran. Telling Sol the rule explicitly barely
helped (43/48 still accepted).

[Full findings](research/findings.md) · [Project site](https://wesdalton.github.io/witness/)

## The idea in 30 seconds

Two runs of the same task. In one, the agent fixed the bug and the tests pass. In
the other, the library calls `os._exit(0)` on import, so the test process exits
cleanly before any test runs. The harness reports "8 passed" for both.

| Evidence the auditor sees | Valid run | Invalid run | Justified verdict |
| --- | --- | --- | --- |
| Harness report only | identical bytes | identical bytes | `insufficient` |
| Auditor-run replay | `8 passed`, exit 0 | no output, exit 0 | `supported` / `refuted` |

Because the report bytes are identical, no auditor can beat a coin flip on the
pair from the report alone, so `insufficient` is provably the right answer. That
lets the benchmark score *whether the auditor knows what it doesn't know*, not
just whether it guesses the label.

## Results (v2, held-out tasks)

8 held-out tasks, 64 incidents, 2,112 episodes, $2.69. Protocol frozen before
dispatch.

| Measure | GPT-6 Luna | GPT-6.1 Sol |
| --- | --- | --- |
| Accepts a replay with exit 0 and no test summary | 48/48 | 48/48 |
| ...after being told the rule | 14/48 | 43/48 |
| Commits to a verdict from a report that cannot decide the claim | 191/192 | 172/192 |
| ...after being told the rule | 0/192 | 0/192 |

The exit-status cells are 8 incidents sampled 6 times; the report-only cells come
from 24 distinct reports. Details, intervals and limitations are in
[research/findings.md](research/findings.md). A replication on DeepSeek, Gemini
and Claude Sonnet is mostly run and not yet analyzed.

## How the benchmark works

- **Paired incidents from real runs.** Small Python libraries run in a locked-down
  Docker container (no network, read-only, all capabilities dropped). Three
  failure families: a shadowed or short-circuited test runner, a timeout recorded
  as success, and failed attempts dropped from a success rate.
- **Access sets.** The auditor gets the harness report plus any combination of
  full artifacts, an independent run manifest, and a replay it controls (8 sets).
- **Certified insufficiency.** A gate checks, for every pair and access set,
  whether the valid and invalid prompts are byte-identical, and that no label
  leaks through names or wording.
- **Executable ground truth.** Two reference checks per label, plus deterministic
  baselines: an exact checker that abstains only when it should, and a naive one
  that never abstains.
- **Pre-registered and budget-capped.** Each paid batch has a frozen protocol, and
  every request goes through an append-only spend ledger that refuses calls over
  the ceiling. See [METHODS.md](METHODS.md).

## Repository layout

| Path | Contents |
| --- | --- |
| [`witness/core/`](witness/core/) | Spend ledger, model client, Docker sandbox, write-once evidence archive |
| [`witness/evidence_access/`](witness/evidence_access/) | Fixture tasks, corpus builder, auditor prompts, baselines |
| [`docker/`](docker/) | The sandbox image the fixture runs use |
| [`scripts/`](scripts/) | Corpus gates, per-stage runners and analyses, archive audits |
| [`tests/`](tests/) | Unit tests for the ledger, archive and benchmark |
| [`research/findings.md`](research/findings.md) | The current report |
| [`research/experiments/`](research/experiments/) | Frozen protocols, gates, raw episodes, analyses and reports for v1 to v3 |
| [`research/registry/`](research/registry/) | SHA-256 records of every sealed evidence bundle |
| [`research/budget.jsonl`](research/budget.jsonl) | Append-only ledger of every paid request |
| [`website/`](website/) | The project site |

## Reproduce

Requires Python 3.12+.

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]' -c requirements-dev.lock

# Recompute the v2 results from the raw episodes (no model calls)
.venv/bin/python scripts/evidence_access_stage2.py \
  --corpus research/experiments/20261031-evidence-access-v2/gates/corpus-v2 \
  --runs research/experiments/20261031-evidence-access-v2/runs/stage2-luna-01 \
         research/experiments/20261031-evidence-access-v2/runs/stage2-sol-01 \
  --out /tmp/witness-v2
cmp /tmp/witness-v2/analysis.json \
    research/experiments/20261031-evidence-access-v2/analyses/stage2-01/analysis.json

# Tests, lint, and integrity checks over all sealed evidence
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/python scripts/research_archive.py audit
.venv/bin/python scripts/audit_research_coverage.py
```

Rebuilding the corpus or running auditors requires Docker and an OpenRouter key,
and spends money; read [METHODS.md](METHODS.md) first.

## History

The project started in October 2026 as a simulation of whether agents in a swarm
stop checking claims when their peers agree. Five early studies on that theme hit
ceilings or were underpowered; [findings](research/findings.md#earlier-studies-closed)
summarizes them and what they taught. Their code and evidence are preserved at
the tag [`archive/2026-11-full`](https://github.com/wesdalton/witness/tree/archive/2026-11-full).

## How this was built

I chose the research question, set the design rules in [METHODS.md](METHODS.md),
approved every protocol and spend, and reviewed the results. Much of the code and
many of the writeups were produced with an AI coding agent (Factory Droid)
working under those rules; commits it co-authored are marked as such.

## License and citation

MIT. Cite with [`CITATION.cff`](CITATION.cff).
