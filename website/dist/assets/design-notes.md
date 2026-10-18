# Design references and interpretation

Witness uses an understated research interface: a visible configuration, an inspectable
network, adjacent measurements, and downloadable evidence. The design is intended to
make model assumptions harder to miss, not make synthetic outcomes look authoritative.

The prior art was checked on 18 October 2026:

- [Inspect View](https://inspect.aisi.org.uk/log-viewer.html) connects aggregate results
  to sample-level messages, scores and metadata. Witness follows the aggregate-to-agent
  path and keeps configuration and resource costs near the measurements.
- [Inspect evaluation logs](https://inspect.aisi.org.uk/eval-logs.html) treat run state,
  configuration and errors as inspectable artifacts. Witness's decision harness records
  a manifest, event stream, errors, usage and completion status; failed decisions remain
  visible rather than disappearing from the denominator.
- [Petri's transcript viewer](https://alignment.anthropic.com/2025/petri/#transcript-viewer)
  distinguishes participant-visible context from an observer's overview and links claims
  to transcript evidence. Witness explicitly separates observer ground truth from agent
  evidence, and differentiates a direct probe from a relayed copy of the same root.

These are interaction precedents, not claims of feature parity or borrowed visual
assets. We retain a small surface area: no chat interface, ornamental dashboards,
leaderboard, fabricated activity feed, or implied live-model execution.

Comparisons prioritize interpretable quantities. Terminal accuracy alone can hide
transient failures, so peak and time-averaged mistakes accompany checking expenditure.
The graph is an inspection aid; numerical exports remain the analysis artifact.
Keyboard access and textual status provide alternatives to color and canvas selection.

The public demo executes locally in the browser. It does not require an account or a
provider key. Public visitors cannot trigger paid model calls. Real-model experiments
are a separate local workflow with explicit model selection and call ceilings.
