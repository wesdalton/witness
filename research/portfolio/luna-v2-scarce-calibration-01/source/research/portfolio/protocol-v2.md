# Portfolio v2: repaired contracts and regression diversity

24 October 2026. Supersedes v1 for new inference only. Raw v1 results, labels,
source snapshots, counterexamples, and adjudication remain unchanged.

## What changed and why

The first capable auditor disproved two v1 positive labels. We preserve those
failures as negative residual variants. Positive multipart and callback
candidates now have explicit local benchmark repairs, implemented in
swarm_lab/portfolio_v2_cases.py. Vendor sources remain unchanged.

Multipart retains suffixes that can still form a boundary, including a partial
closing marker. Callback processing publishes PROMPT before processing the
prompted value. These are local experimental repairs, not upstream releases or
claims of production-ready fixes. All variants retain upstream licenses.

Model-facing contracts identify the regression scope. The multipart scope
includes all short a/CR/LF payloads through length four and near-64-KiB zero-filled
payloads, single file, valid complete CRLF headers, and chunk boundaries. Callback
scope includes all five named sources, initial prompt processing, and shared
flag destinations. Routing covers 1–16 nonnegative integer converters in a segment.
Counterexamples within those contracts invalidate a label regardless of whether
our hidden tests anticipated them. A finite gate is not a universal correctness proof.

The free gate runs ordinary smoke tests plus expanded reference checks:
21,686 multipart conditions, 29 callback conditions, and sixteen routing
conditions. Uniform chunk widths and all two-way splits are covered for the
short payloads; not every possible multipart partition is enumerated. The
long-payload checks place the default 64-KiB buffer boundary around the closing
delimiter. The callback test specifies a default only on the positive flag,
avoiding an ambiguous pair of explicit competing defaults.

The gate must accept repaired positives and reject both historical regressions
and the two residual variants. V1 remains disabled. V2 cannot dispatch until
this full gate passes again in the recorded immutable container image.

## Constants and design

Retain v1's six-claim portfolio, independent truth/order/target random streams,
equal-weight Brier scoring, per-case investigation credits, maximum 24 commands,
maximum sixteen responses, isolated execution, and strict per-case citations.
Add an independent seed/index-based stream choosing historical or residual
negative variants for multipart and callbacks. Positive variants always use
the same repaired source. Routing has only its historical negative.

All arms still share the same source candidates for a matched seed. Initial smoke
reports are identical across labels and variants. There is no true-count hint.
The arithmetic control can be answered without inspecting a workspace.

First repeat the no-peer capable-model calibration on seed 1001 with six credits.
Keep model/settings unchanged so a new API configuration is not another cause.
Then review actual probes, source reasoning, labels, cost, and completeness before
any scarce-budget or peer batch. The decision log specifies each next batch.

## Research claims and accounting

The [novelty review](novelty-review.md) narrows the intended contribution to
autonomous probe construction and its fault coverage under peer influence.
This v2 capability calibration is a validity prerequisite, not that experiment.
No novel behavioral result follows from passing it.

After the two Sol calibrations, an optional navigation-hint configuration supplies
the package-root layout and available grep utility. This removes an observed
wasted attempt to use src/ and an unavailable rg binary. It gives no source
contents or label. The flag is recorded per episode and in its exact system
prompt; do not pool prompted and unprompted calibrations as a model comparison.
All arms of a subsequent comparison must use the same flag.

The Luna input reservation ceiling is raised from the earlier arbitrary 60,000
bound to 160,000, including JSON overhead. A valid Sol calibration reached 61,460,
so retaining the old bound would create a predictable infrastructure failure.
[Official Luna documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
places long-context pricing above 272,000 input tokens. The new bound remains
below that threshold. Catalog and rate checks remain mandatory; every request is
reserved at the full conservative bound and checked against returned usage.

All paid calls use the same phase ledger and $25 total cap. Freeze this protocol,
implementation, decisions, prompts, model metadata, vendor bytes, and image ID.
Preserve failures; no automatic retries or fallbacks. Stop on Daybreak rejection
without alternate routes. A normal code/test failure can be diagnosed locally;
it is not grounds to abandon the research loop.
