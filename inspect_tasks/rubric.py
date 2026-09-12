"""Rubric formatting and grader-output parsing for the adversarial_reasoning task.

Pure functions only (no model calls) so they can be unit tested with fixtures.

The grader is asked to emit one verdict line per criterion:

    C1: PASS - one-sentence justification
    C2: FAIL - one-sentence justification
    ...
    SUMMARY: one sentence

`parse_grader_output` is deliberately forgiving about surrounding reasoning text
and strict about the verdict tokens: a criterion with no parseable verdict is
reported as missing, not silently treated as FAIL, so the scorer can decide what
to do (it marks the sample unscored rather than inventing a grade).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# `[\s*]*` absorbs the markdown bold markers models like to sprinkle around tokens.
VERDICT_RE = re.compile(
    r"^[\s*]*C(?P<idx>\d+)[\s*]*:[\s*]*(?P<verdict>PASS|FAIL)\b[\s*]*"
    r"(?:[-:–—][\s*]*(?P<why>.*))?$",
    re.IGNORECASE | re.MULTILINE,
)
SUMMARY_RE = re.compile(r"^[\s*]*SUMMARY[\s*]*:[\s*]*(?P<text>.+)$", re.IGNORECASE | re.MULTILINE)


@dataclass
class CriterionVerdict:
    index: int  # 1-based, matches C<n>
    passed: bool
    justification: str = ""


@dataclass
class RubricResult:
    verdicts: list[CriterionVerdict]
    missing: list[int] = field(default_factory=list)
    summary: str = ""

    @property
    def n_passed(self) -> int:
        return sum(v.passed for v in self.verdicts)

    @property
    def complete(self) -> bool:
        return not self.missing

    def fraction(self, n_criteria: int) -> float:
        return self.n_passed / n_criteria if n_criteria else 0.0


def format_rubric(criteria: list[str]) -> str:
    """Render criteria as a numbered list the grader can reference by id."""
    return "\n".join(f"C{i}. {c.strip()}" for i, c in enumerate(criteria, start=1))


def parse_grader_output(text: str, n_criteria: int) -> RubricResult:
    """Extract per-criterion verdicts from free-form grader text.

    If a criterion id appears more than once, the last occurrence wins (models
    sometimes think out loud with a provisional verdict, then restate). Ids outside
    1..n_criteria are ignored.
    """
    found: dict[int, CriterionVerdict] = {}
    for m in VERDICT_RE.finditer(text):
        idx = int(m.group("idx"))
        if not 1 <= idx <= n_criteria:
            continue
        found[idx] = CriterionVerdict(
            index=idx,
            passed=m.group("verdict").upper() == "PASS",
            justification=(m.group("why") or "").strip().rstrip("*").strip(),
        )

    verdicts = [found[i] for i in sorted(found)]
    missing = [i for i in range(1, n_criteria + 1) if i not in found]
    summary_match = SUMMARY_RE.search(text)
    summary = summary_match.group("text").strip() if summary_match else ""
    return RubricResult(verdicts=verdicts, missing=missing, summary=summary)
