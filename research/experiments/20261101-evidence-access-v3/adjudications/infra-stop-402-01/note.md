# Infrastructure stop: OpenRouter account credit exhausted (HTTP 402)

Recorded 7 November 2026 (machine clock). No retry was made.

## What happened

The v3 Sol batch (`stage3-gpt-6-1-sol-01`) completed 512 of 1,056 episodes. Its
next request, at 2026-11-01T04:23:56Z, returned HTTP 402 (payment required), and
the runner stopped. That request was never served and is not billed by the
provider. The ledger keeps its full reservation.

A free read of the key status on 7 November showed:

| Item | Value |
| --- | --- |
| Key cap | $100, non-resetting; $90.05 remaining |
| Account credits | $10.00 total, $9.945 used |

The binding limit is the account's prepaid credit, not the key cap. Provider
usage ($9.945) reconciles with our ledgers: the phase ledger records $9.933
billed and the 18 October pilot ledger $0.011, together $0.001 below the provider
figure.

## State

- DeepSeek and Luna are complete.
- Gemini has 1,023 of 1,056 episodes; its continuation is approved.
- Sol has 512 of 1,056 episodes.
- Sonnet has not started.

Finishing v3 as amended needs about $14 more provider credit.

## Correction to amendment 01

The sealed `protocol-amendment-01` is dated "1 November 2026". The machine clock
shows it was written and sealed on 7 November 2026, as its ledger row records.
Its content and decisions are unchanged.
