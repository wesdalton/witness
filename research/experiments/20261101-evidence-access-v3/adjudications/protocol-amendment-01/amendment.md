# Protocol v3 amendment 01: budget, Gemini continuation, Sonnet ceiling

1 November 2026. Written after the DeepSeek run finished and the Gemini run
stopped. It was written before any v3 result was analyzed, and before Sonnet,
Luna or Sol ran under v3. No question, cell, prompt, sample count or analysis
changes.

## What happened

The Gemini 3.8 Flash batch stopped at its frozen $4.00 ceiling after 1,023 of
1,056 episodes. Every response settled normally, and none failed. Its mean cost
was $0.0039 per episode, about twice the smoke-test estimate. The counts arm and
the full-access cells produce longer outputs than the four smoke episodes
suggested. The stopped run is sealed as `stage3-gemini-3-8-flash-01`.

Projected from Gemini's actual per-cell costs and the Sonnet/Gemini smoke ratio
(3.0×), Sonnet 5.5 would cost about $12.40, above its frozen $8 ceiling. Finishing
v3 as frozen would bring the phase to about $26, above the $25 phase ceiling.

## Decisions (user-approved, 1 November 2026)

1. **Phase ceiling raised from $25 to $35.** This is recorded as an
   `authorization_amendment` row in `research/agent-study/budget.jsonl`. The
   original header row is unchanged.
2. **Gemini continuation.** The 33 unattempted episodes of the same plan run as a
   new batch, `stage3-gemini-3-8-flash-02`, with a $0.50 ceiling, linked to the
   stopped run. No episode is repeated. The analysis pools the two runs by model
   and rejects duplicate episode IDs.
3. **Sonnet 5.5 batch ceiling** raised from $8 to $15, set before dispatch.
4. Luna ($1.50) and Sol ($6) ceilings are unchanged.

## Analysis-script change

`scripts/evidence_access_stage3.py` now groups runs by model so a continuation
pools with its parent. Results are keyed by model name. The statistics,
thresholds and tests are unchanged.
