# Initial live-pilot plan

Prepared 18 October 2026, before any live inference in this project.

## Purpose and stopping rules

This pilot checks whether the decision environment works with real models and whether
there is enough behavioral variation to justify the proposed study. It is not a
confirmatory test, a leaderboard, or a population-scale alignment claim.

Begin with four agents, four synchronous rounds, the false-report fixture, report-only
context, seed 42, and verification delay two. Sixteen decisions allow a check requested
in round one to arrive in round three and influence a subsequent response. Inspect
validity, provider/model identity, actual usage, source references, budget charges,
and the observation delivered after checking.

Stop on authentication, credit, price-cap or billing-contract errors. Diagnose
systematic malformed output or truncation before collecting a matrix. Any prompt or
model-setting change receives a distinct artifact and is reported; do not silently
combine earlier and later conditions.

After calibration, use matched true/false fixtures and reports/ancestry/reserved
policies, initially eight agents and eight rounds. The first matrix has one seed;
expand to additional seeds only after reviewing completion and measurement quality.
Expansion stays within the cumulative US$100 authorization. A small initial batch
reserves at most US$5, with no obligation to spend that much or exhaust the total.

## Model selection

The first candidate is `openrouter/openai/gpt-6-luna` routed to OpenAI's standard
endpoint, with reasoning disabled. This is an inexpensive infrastructure calibration,
not a claim to cover frontier behavior. The public catalog and endpoint metadata were
checked on 18 October 2026. Standard short-context prices at that check were US$0.10
per million input tokens and US$0.50 per million output tokens. Revalidate them before
execution and pin price ceilings rather than accepting dynamic router defaults.

Official references:

- [OpenAI model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
  specifies its supported reasoning modes.
- [OpenAI token accounting](https://developers.openai.com/api/docs/guides/token-counting)
  explains that output caps include non-visible generated tokens.
- [OpenRouter model catalog](https://openrouter.ai/docs/api/api-reference/models/get-models)
  exposes provider/model metadata and prices.
- [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)
  supports provider restrictions and maximum price filters.
- [OpenRouter reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
  documents model-specific behavior; disabling reasoning is not valid for every model.

Later family comparisons require separate verified billing and parameter contracts.
Candidate families include Anthropic and Google, but they are not preapproved by a
generic reasoning-off flag. Do not infer capability rankings from their marketing
position or assume that a shared output limit allocates identical reasoning effort.

## Evidence and analysis

Preserve raw public decisions, model-visible context, the run manifest, receipt IDs,
actual provider usage, completion errors, and the budget reservation ledger. Keep
credentials outside artifacts. Paid runs use an explicit live mode; dry-run planning
is the default. Retry behavior and provider fallback must be disabled.

`python -m swarm_lab.analyze` creates one row per completed episode, keeping scripted
smokes separate from model experiments. It reports terminal and mean error, uncertain
agents, Brier score, unique agents checking, requests, deliveries, used/unused action
budget and token usage. It rejects missing rounds and broken action accounting.

Report true and false fixtures together. These two ledger variants are one case
family. Neither their agents nor their repeated seeds establish broad task diversity.
Any apparent communication effect is exploratory until exposed to the randomized
branching and held-out cases described in the main protocol.

## Operational amendments, 18 October 2026

The 16-decision calibration completed. An expanded batch stopped after a provider
error; a later fresh attempt identified HTTP 429 after 20 successful requests.
The first attempted restart also exposed a runner bug: duplicate request IDs were
checked across batches instead of within each batch. That attempt dispatched no
requests. Batch-scoped uniqueness is now regression-tested; every original artifact
and reservation is retained.

A fresh matched true/false report-only pair uses eight agents and eight rounds,
with a 3.2-second minimum interval between request starts. This pacing is an
operational response to the observed rate limit, not a change to simulated rounds
or model context. It is recorded in the batch manifest. Remaining treatment arms
will follow only after this pair passes measurement review. The initial matrix is
therefore incomplete; do not present the report-only pair as an intervention comparison.

The paced true-report episode completed all 64 calls with seven malformed JSON
responses and no provider failure. The runner then stopped the remaining matrix.
Inspection found extra text following JSON objects; these responses remain recorded
as invalid and were not repaired. The matching false fixture was collected separately
under identical settings, completing 64 calls without parsing or provider errors.
See the [pilot report](pilot-report.md) for both outcomes and the retained failures.
