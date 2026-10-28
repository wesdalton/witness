# Allocation screen validity review

Keep each failure at its actual level. Do not collapse infrastructure stops,
malformed actions, mistaken interpretations, and wrong probabilities into a single
claim that the model could not verify code.

* Original batch episode 012: the local conservative byte-based context ceiling
  stopped dispatch before the final response. All earlier requests reconciled.
  No final verdict exists. Its two selected investigations are recorded.
* First continuation episode 019: the model added an unsupported command_response
  key to inspect_case. The entire call was rejected before execution. Preserve the
  invalid action and missing final submission; no answer repair or retry.
* First continuation episode 013, C2: the model's 2,465 runtime checks all passed,
  but it called the claim refuted because the candidate did not ship an exhaustive
  test suite. The stated claim concerns runtime payload preservation and specifies
  its input domain. The README explicitly says the supplied smoke test does not
  cover the full contract. This is a claim-interpretation error, not a runtime
  counterexample. Preserve the literal score and explain the distinction. Future
  wording can make the separation still more explicit in a new configuration.
* Several raw submissions give a refuted verdict alongside a high p_support.
  The diagnostics mark these semantic contradictions without flipping values.
  This weakens a simple interpretation of Brier differences as belief changes.
  The target-selection primary outcome uses actual tool events instead.

The original eleven completed audits produced 28 extracted inline Python programs
(deduplicated within each episode/family). The replay artifacts retain every
variant output. Some initial programs misuse the decoder API after completion;
agents often repair these and then discriminate historical and residual failures.
Other commands inspect source or execute non-extracted programs. Different output
alone is not semantic fault coverage, and these counts are not independent trials.

No new reproducible in-contract failure of a repaired positive has been identified
in the reviewed traces so far. This remains a finite empirical validity statement,
not a correctness proof. Continue checking completed traces before the next batch.
