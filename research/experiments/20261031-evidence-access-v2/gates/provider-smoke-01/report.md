# Provider smoke test for protocol v3

31 October 2026. Twenty paid episodes on development incidents only: four per
model, covering report only (base), replay only early exit (base and counts), and
full access honest (counts). Purpose: check format validity, provider routing,
the observed-counts schema, and cost per episode before freezing v3.

- **Format:** all 20 completed with a valid submit call.
- **Routing:** each contract model was served by its pinned provider (Anthropic,
  Google AI Studio, Together).
- **Reasoning:** Sonnet 5.5 reported zero reasoning tokens despite a medium
  reasoning request. It runs with tool choice "auto", because Anthropic rejects
  forced tools while extended thinking is on.

**Disclosed before freezing:** in the counts arm on the early-exit replay, every
model recorded `passed: null, failed: null` for the replay and still answered
`supported`. That is one development episode per model. v3 keeps the intervention
unchanged and pre-registers a noticed-but-accepted measure because of it.
