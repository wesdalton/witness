# Methods

These are the rules every paid experiment in Witness follows. I adopted them after
five early studies produced no finding (see [findings](research/findings.md#earlier-studies-closed)).
The causes were weak treatments, underpowered comparisons, and tasks at a
capability ceiling. Each rule below prevents one of those, or protects the
evidence.

## Design

1. **Freeze before dispatch.** Before any paid batch, write down the question,
   primary endpoint, smallest effect worth detecting, sample size, exclusions,
   analysis, stopping rule and maximum spend, and commit it.
2. **Power first.** Compute the sample size needed to detect the smallest effect at
   the frozen alpha. Do not run a comparison that cannot detect it. A small pilot
   to estimate variance is allowed if it is labeled as a pilot.
3. **Calibrate difficulty before comparing treatments.** On development tasks with
   no treatment, adjust difficulty until the baseline outcome sits roughly between
   30% and 70%. Never tune on treatment-arm outcomes, and never reuse development
   tasks for the test set.
4. **Use a real treatment dose.** Stimuli must be plausible and strong enough to
   matter, with dose levels where possible. Do not prime the model against the
   manipulation unless that priming is itself a varied factor.
5. **Ground truth is executable.** Labels come from at least two independent
   reference checks, not from an LLM's opinion. Paired cases must not leak the
   label through names, hashes, sizes, wording or ordering.
6. **Count units honestly.** The unit of analysis is the independent incident.
   Repeated samples of one prompt are not independent. Cluster uncertainty at the
   right level and say how many distinct stimuli a number rests on.
7. **Report every outcome.** Nulls count. Keep simulations, scripted checks,
   recorded-observation agents and live agents clearly separate.

## Evidence

- **Write-once outputs.** Every run gets a unique ID and a folder that is never
  overwritten.
- **Sealed bundles.** A completed or stopped run, gate, analysis or report is
  sealed: [`witness/core/archive.py`](witness/core/archive.py) records the SHA-256
  of every file in [`research/registry/`](research/registry/), and
  `scripts/research_archive.py audit` detects any later change, addition or
  deletion.
- **Corrections are adjudications.** A mistake in sealed evidence is never fixed
  in place. It gets a separate, sealed note that explains it, such as the
  [dropped-attempts label defect](research/experiments/20261031-evidence-access-v2/adjudications/dropped-attempts-labels-01/adjudication.md).
- **Stops are recorded.** When a run stops early for any reason, the stop is
  written down and the run is sealed as stopped. Failed requests are not retried.

## Spending

[`witness/core/budget.py`](witness/core/budget.py) keeps an append-only ledger,
[`research/budget.jsonl`](research/budget.jsonl), under a file lock:

- Before each request, it reserves the worst-case cost (input bound plus maximum
  output at the provider's price) and refuses the request if the phase or batch
  ceiling would be exceeded.
- A request settles at the provider-reported cost. A failed or unpriced request
  keeps its full reservation, and a request that costs more than its reservation
  counts at its actual cost.
- Any unsettled or failed request blocks further spending until it is reviewed.
- The client pins one provider with no fallbacks and a maximum price, and refuses
  to run with an API key that lacks a non-resetting spend cap.

The ceiling is set by the ledger's header row plus explicit amendment rows; the
ledger is never reset or rewritten.
