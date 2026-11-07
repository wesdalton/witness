# Protocol v3 amendment 02: Sol continuation after the credit stop

7 November 2026. Written before any v3 result was analyzed and before any further
dispatch. No question, cell, prompt, sample count or analysis changes.

The Sol batch stopped after 512 of 1,056 episodes on an HTTP 402. The OpenRouter
account had exhausted its prepaid credit; see `infra-stop-402-01`. The user will
add credit and signal when to resume.

## Decisions

1. **Sol continuation.** The 544 unattempted episodes of the same plan run as
   `stage3-gpt-6-1-sol-02`, linked to the stopped run, with a $4.48 ceiling. The
   first batch billed $1.52 and reserved $0.057 for the failed request, so Sol's
   total exposure stays within the frozen $6.00. No episode is repeated.
2. **Order on resume.** Sol continuation, then the Gemini continuation (amendment
   01, $0.50), then Sonnet 5.5 (amendment 01, $15). The ledger allows only one
   spending batch at a time.
3. **Credit check.** Before each batch, a free key-status read must show account
   credit at least equal to that batch's ceiling. If it does not, stop and record.
