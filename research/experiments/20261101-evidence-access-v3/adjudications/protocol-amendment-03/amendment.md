# Protocol v3 amendment 03: finish v3 after the repository restructure

16 November 2026. Written before any v3 result was analyzed and before any further
dispatch. No question, cell, prompt, sample count or analysis changes. The owner
approved finishing v3 as below on 16 November 2026.

## What changed since amendment 02

- The Sol continuation finished (544/544). The Gemini continuation stopped after
  11 of 33 episodes when request `0be749382d5c482e90d54953a7f0ec6b` (episode 1034)
  timed out with an unknown outcome; see `infra-stop-timeout-01`. Sonnet 5.5 has
  not started.
- The repository was restructured on 16 November. The package `swarm_lab` is now
  `witness`, and the phase ledger moved to `research/budget.jsonl` with its bytes
  unchanged. Two code changes affect the runner:
  1. Budget exposure now counts a failed request that reports a cost above its
     reservation at the reported cost. No v3 request has done so, so every past
     exposure figure is unchanged.
  2. A continuation may follow several earlier runs and may skip episodes that an
     earlier run attempted without writing a record. Skipped episodes are never
     repeated.
  Prompts, submit tools, plans, models, provider contracts, reasoning settings and
  request construction are unchanged. Dry runs give the planned episodes below.
  New run manifests record their source under `witness/` with new hashes.

## Decisions

1. **Gemini continuation 03.** The 21 episodes that neither earlier Gemini run
   attempted run as `stage3-gemini-3-8-flash-03`, continuing from
   `stage3-gemini-3-8-flash-01` and `-02`, with a $0.44 ceiling: amendment 01's
   $0.50 continuation budget less the $0.054 exposure of `-02`. Episode 1034 is
   not repeated and is analyzed as missing, so Gemini has at most 1,055 of 1,056
   planned episodes.
2. **Sonnet 5.5.** The full plan of 1,056 episodes runs as
   `stage3-claude-sonnet-5-5-01` with the $15 ceiling set in amendment 01.
3. **Order and credit.** Gemini continuation 03, then Sonnet. A free key-status
   read on 16 November showed $23.44 of account credit and $23.38 of phase
   headroom, enough for both ceilings, as amendment 02 requires.
4. **Stops.** Any provider error, ceiling stop or rejected action ends that batch.
   It is recorded and not retried.
5. **Analysis.** After both batches, the frozen analysis
   (`scripts/evidence_access_stage3.py`) runs once over every v3 run, pooling
   continuation runs by model. Results are reported in full whatever they show.
