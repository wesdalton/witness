from pathlib import Path

import pytest

from inspect_tasks.rubric import format_rubric, parse_grader_output

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_format_rubric_numbers_from_one():
    out = format_rubric(["  first ", "second"])
    assert out == "C1. first\nC2. second"


def test_clean_output_parses_every_criterion():
    r = parse_grader_output(fixture("grader_clean.txt"), n_criteria=5)
    assert r.complete
    assert [v.passed for v in r.verdicts] == [True, True, False, True, True]
    assert r.verdicts[2].justification == "Computes 40% of 441 instead of 735."
    assert r.n_passed == 4
    assert r.fraction(5) == pytest.approx(0.8)
    assert r.summary.startswith("Right answer")


def test_markdown_bold_case_and_dash_variants_are_tolerated():
    r = parse_grader_output(fixture("grader_markdown_noise.txt"), n_criteria=4)
    assert r.complete
    assert [v.passed for v in r.verdicts] == [True, False, True, False]
    assert r.verdicts[0].justification == 'the response gives exactly "13,11,7,5,3".'
    assert r.verdicts[3].justification == ""  # bare verdict with no reason
    assert r.summary == "Mostly right."


def test_last_verdict_for_a_criterion_wins():
    r = parse_grader_output(fixture("grader_restated.txt"), n_criteria=3)
    assert r.complete
    assert r.verdicts[0].passed is True
    assert r.n_passed == 3


def test_missing_and_out_of_range_ids_are_reported_not_guessed():
    r = parse_grader_output(fixture("grader_missing.txt"), n_criteria=4)
    assert not r.complete
    assert r.missing == [2, 4]
    assert [v.index for v in r.verdicts] == [1, 3]  # C7 ignored
    assert r.summary == ""


def test_empty_output_is_all_missing():
    r = parse_grader_output("", n_criteria=3)
    assert r.missing == [1, 2, 3]
    assert r.fraction(3) == 0.0


def test_verdict_word_must_be_pass_or_fail():
    r = parse_grader_output("C1: MAYBE - unsure\nC2: PASSED - yes", n_criteria=2)
    assert r.missing == [1, 2]
