# inspect-tasks

Two [Inspect AI](https://inspect.aisi.org.uk) evaluation tasks, built as a work sample for
METR's Task Development Engineer role. This is my first Inspect work: I read the 0.3.263
source for the scorer/sandbox APIs rather than guessing, and the commit history shows
the order I built things in (smoke test → task 1 → task 2 → unit tests → this README).

## How to run

```bash
uv venv && source .venv/bin/activate      # or python -m venv
uv pip install -e ".[dev]"                # pins inspect-ai==0.3.263
export ANTHROPIC_API_KEY=...              # or OPENAI_API_KEY, GOOGLE_API_KEY, etc.

inspect eval smoke/hello.py --model anthropic/claude-sonnet-5              # toolchain check
inspect eval inspect_tasks/adversarial_reasoning.py --model anthropic/claude-sonnet-5
inspect eval inspect_tasks/sandbox_coding.py --model anthropic/claude-sonnet-5  # needs Docker
inspect view                                                              # browse logs/
```

Any Inspect provider string works (`openai/...`, `google/...`, `openrouter/...`). The
model under test grades task 1 by default; to use a separate grader add
`--model-role grader=<provider/model>`. Dev checks: `pytest`, `ruff check .`, and
`python scripts/sandbox_scenarios.py` (drives six scripted agents through the real
Docker pipeline and asserts each scorer verdict).

## Results

**No real-model run yet.** The machine this was built on had no provider key, and I
was not going to fabricate a results table. What *has* been verified:

| Check | Result |
|---|---|
| `smoke/hello.py`, `mockllm/model` | runs end to end, scores 0 (mock output is canned) |
| `adversarial_reasoning`, mockllm with scripted verdicts | 4/4 samples scored, `mean=0.675` as expected from the script |
| `sandbox_coding`, scripted agents via Docker (`scripts/sandbox_scenarios.py`) | honest fix → C; no change, symptom-only fix, edited test, deleted test, added conftest → I |
| `pytest` | 14 passed |
| `ruff check .` | clean |

To produce real numbers, run the three `inspect eval` commands above with a key
exported, then paste the `mean` / `strict_accuracy` / `accuracy` lines and the model
string and date here. If a run errors, put the error here instead.

**Scorer integrity pilot (18 October 2026).** A later local subprocess reproduction
found two false successes under the coding task's scoring rule: exiting during library
import and substituting a workspace module for pytest. Both preserve protected test
files. The original scorer is therefore a vulnerable baseline for this threat model.
The [pilot and research proposal](research/directions.md) include reproducible code,
recorded evidence, and three possible open-source directions. These new fixtures have
not yet been run through the full Inspect/Docker pipeline; no model behavior is claimed.

## Design notes

**adversarial_reasoning** measures whether a model can hold a multi-step problem
steady under distractors, conflicting instructions, false premises, and long-context
state changes, without falling back on pattern-matched answers. The way this becomes a
bad measurement is grader slop: a single "is it correct?" judgment lets a fluent wrong
answer through and lets the grader's own priors leak in. So every item carries 3-5
literal, independently checkable criteria (`data/adversarial_reasoning.jsonl`), the
grader must emit one `C<n>: PASS|FAIL - why` line per criterion, and the score is the
fraction met; `strict_accuracy` reports how often *all* criteria pass. If any verdict
is missing the sample is left unscored (NaN) rather than guessed at, and every
justification is stored in score metadata so bad grading is auditable in `inspect view`.
Items `st-01` to `st-04` are shortcut traps: the surgeon riddle where the mother died,
Monty Hall with a host who opens doors at random, bat-and-ball with the bat price given
directly, and the river crossing with a boat that fits everyone. Each looks like a
famous puzzle whose memorised answer is wrong here, and each rubric has a criterion
that fails on the memorised answer specifically. Every item has a single reference
answer that I worked by hand (arithmetic re-checked in Python).

**sandbox_coding** measures whether an agent can read a spec, find a bug from one
failing test, and fix the *cause* rather than the symptom. The container holds a small
ledger library whose date-range helper uses an exclusive end bound; the one visible
failing test only exposes this through `balance(as_of=...)`, but `statement()` shares
the helper. A 20-test hidden suite (`sandbox/hidden_tests/`, written into `/opt` after
submission, never on the agent's path) covers the whole spec, so a fix that patches
`balance` alone scores 0. The obvious way to make this a bad measurement is letting the
agent make the visible test pass by editing it, so a setup solver sha256-snapshots
`tests/**` plus every pytest config file pytest would read (`conftest.py`,
`pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`) before the agent starts; the
scorer re-snapshots at grading time and any modified, deleted, or added path is an
automatic 0 with the diff in the explanation. Bytecode caches are excluded because the
first scripted run flagged `tests/__pycache__` after the honest agent ran pytest - that
false positive is why the scenario script exists. The container has no network and
1 CPU / 512 MB.

## What I'd build next

- **Grader calibration for task 1.** Hand-grade ~30 model outputs against the same
  rubrics, compute per-criterion agreement with the model grader, and drop or rewrite
  any criterion under 90% agreement. Right now the rubric precision is asserted, not
  measured.
- **A difficulty ladder for task 2.** Same harness, three more repos: a bug that needs a
  new test to even reproduce, a two-file refactor where hidden tests check an
  invariant not a value, and one where the honest fix is slower than the hack so the
  scorer also has to time the suite. Each gets a scripted-agent scenario file like the
  one here before any real model runs.
- **Snapshot the whole workspace, not just tests.** Diff the agent's tree against the
  original at scoring time and record the patch in metadata, so a reviewer can see
  *what* changed in one place instead of replaying tool calls, and so "hardcoded the
  answer" becomes a greppable pattern across runs rather than a per-sample judgment.
