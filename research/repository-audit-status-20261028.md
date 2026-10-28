# Repository-audit preparation: stopped before setup

The user approved the next experiment set on 28 October 2026. Source review
identified three candidate historical regressions with exact upstream parent/fix
commits: [attrs converter composition](https://github.com/python-attrs/attrs/pull/1328),
[packaging ordered comparisons](https://github.com/pypa/packaging/pull/1097), and
[Werkzeug bounded-stream reads](https://github.com/pallets/werkzeug/pull/3253).
The unfinished builder is `swarm_lab/repo_cases.py`. No corpus was downloaded,
reference gate executed, experiment registered, or model request dispatched.

The planned capability gate was six fresh reviewer sessions (buggy/fixed versions
of each project), at most eight responses each, with $2 maximum reservations
inside the existing $25 phase. That gate was to precede any peer comparison.
The later candidate question is whether seeing a real earlier reviewer's
conclusion changes additional bug discovery when its test code and execution
results are otherwise identical. It remains a design candidate, not a tested or
novel result. A patched snapshot would be a control for a specific bug, not a
declaration that the whole library is correct.

The automatic PreToolUse guard rejected the combined setup command before execution.
Its reported rule was `(^|[[:space:];&|(])pass[[:space:]]+[^[:space:]]`, matching
ordinary protocol prose containing “pass on”. The response labeled this a global
catastrophic-command denylist rejection and explicitly prohibited retrying or
working around it. The setup was not retried through another command or tool.
The independent archive work continued. A new run must not be claimed complete.

Spending remains 590 recorded phase requests, $0.449982210 provider-reported cost,
and $6.425077750 retained conservative reservations. This turn added zero API spend.
Approval for the research work is already recorded; the obstacle is the automatic
execution guard, not missing budget authorization.
