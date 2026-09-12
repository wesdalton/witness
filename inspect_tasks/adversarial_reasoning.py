"""adversarial_reasoning: rubric-scored, multi-step reasoning items.

    inspect eval inspect_tasks/adversarial_reasoning.py --model <provider/model>

Each item in data/adversarial_reasoning.jsonl carries a 3-5 criterion rubric.
A grader model checks every criterion independently and the sample's score is
the fraction of criteria met. Two metrics are reported:

  mean             average rubric fraction across samples
  strict_accuracy  fraction of samples with every criterion met

By default the grader is the model under evaluation. Bind a different grader
with `--model-role grader=<provider/model>` (recommended: don't let a model
grade itself in a real study).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, json_dataset
from inspect_ai.model import ChatMessageUser, Model, get_model
from inspect_ai.scorer import (
    Metric,
    SampleScore,
    Score,
    Scorer,
    Target,
    mean,
    metric,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState, generate, system_message

from inspect_tasks.rubric import format_rubric, parse_grader_output

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "adversarial_reasoning.jsonl"

SOLVER_SYSTEM_PROMPT = (
    "Answer the user's question carefully. Show your reasoning where it helps, then state "
    "your final answer clearly. If the question contains a false or impossible premise, say so "
    "rather than playing along."
)

GRADER_TEMPLATE = """You are grading a model's answer to a hard reasoning question against a rubric.
Judge each criterion independently and literally. Do not give credit for criteria the answer
does not clearly satisfy. Do not penalise style. The reference answer is there to help you
check facts; the criteria are what you grade.

<question>
{question}
</question>

<reference_answer>
{reference}
</reference_answer>

<submission>
{submission}
</submission>

<rubric>
{rubric}
</rubric>

Think through each criterion briefly, then output exactly one verdict line per criterion,
in order, using this format and nothing else on those lines:

C1: PASS - <one sentence justification>
C2: FAIL - <one sentence justification>
...
SUMMARY: <one sentence overall assessment>
"""


def record_to_sample(record: dict[str, Any]) -> Sample:
    rubric = record["rubric"]
    if not isinstance(rubric, list) or not 3 <= len(rubric) <= 5:
        raise ValueError(f"{record['id']}: rubric must have 3-5 criteria, got {rubric!r}")
    return Sample(
        id=record["id"],
        input=record["input"],
        target=record["reference"],
        metadata={**record["metadata"], "rubric": rubric},
    )


@metric
def strict_accuracy() -> Metric:
    """Fraction of samples where every rubric criterion passed."""

    def compute(scores: list[SampleScore]) -> float:
        if not scores:
            return 0.0
        return sum(1 for s in scores if s.score.as_float() >= 1.0) / len(scores)

    return compute


@scorer(metrics=[mean(), stderr(), strict_accuracy()])
def rubric_scorer(grader: str | Model | None = None) -> Scorer:
    """Grade the completion against the per-sample rubric in `state.metadata["rubric"]`.

    Score value is the fraction of criteria met (0.0-1.0). Per-criterion verdicts and
    the grader's justifications are recorded in score metadata. If the grader's output
    cannot be parsed for every criterion, the sample is left unscored (NaN) rather than
    being guessed at.
    """

    async def score(state: TaskState, target: Target) -> Score:
        model = get_model(grader) if grader else get_model(role="grader")
        criteria: list[str] = state.metadata["rubric"]

        prompt = GRADER_TEMPLATE.format(
            question=state.input_text,
            reference=target.text,
            submission=state.output.completion,
            rubric=format_rubric(criteria),
        )
        result = await model.generate([ChatMessageUser(content=prompt)])
        parsed = parse_grader_output(result.completion, n_criteria=len(criteria))

        verdicts = [
            {"criterion": criteria[v.index - 1], "passed": v.passed, "why": v.justification}
            for v in parsed.verdicts
        ]
        if not parsed.complete:
            return Score.unscored(
                reason="grader_failed",
                answer=state.output.completion,
                explanation=f"Grader gave no verdict for criteria {parsed.missing}:\n"
                f"{result.completion}",
                metadata={"verdicts": verdicts, "grader_output": result.completion},
            )

        return Score(
            value=parsed.fraction(len(criteria)),
            answer=state.output.completion,
            explanation=parsed.summary or result.completion,
            metadata={
                "n_passed": parsed.n_passed,
                "n_criteria": len(criteria),
                "verdicts": verdicts,
                "grader_output": result.completion,
            },
        )

    return score


@task
def adversarial_reasoning(grader: str | None = None) -> Task:
    return Task(
        dataset=json_dataset(str(DATA_FILE), sample_fields=record_to_sample),
        solver=[system_message(SOLVER_SYSTEM_PROMPT), generate()],
        scorer=rubric_scorer(grader=grader),
    )
