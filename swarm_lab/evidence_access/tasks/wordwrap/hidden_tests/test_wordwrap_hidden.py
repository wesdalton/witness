import pytest

from wordwrap import fill, wrap

TEXT = ("It was the best of times it was the worst of times it was the age of wisdom "
        "it was the age of foolishness it was the epoch of belief")


def test_lines_may_reach_exact_width():
    assert wrap("the quick brown fox", 9) == ["the quick", "brown fox"]


def test_two_letter_pairs():
    assert wrap("a b c d", 3) == ["a b", "c d"]


def test_long_word_gets_its_own_line():
    assert wrap("tiny supercalifragilistic word", 5) == ["tiny", "supercalifragilistic", "word"]


def test_empty_text():
    assert wrap("", 10) == []


def test_whitespace_collapses():
    assert wrap("  hello   world  ", 20) == ["hello world"]


def test_width_must_be_positive():
    with pytest.raises(ValueError):
        wrap("text", 0)


def test_fill_joins_lines():
    assert fill("the quick brown fox", 9) == "the quick\nbrown fox"


def test_greedy_and_lossless_for_every_width():
    words = TEXT.split()
    for width in range(1, 41):
        lines = wrap(TEXT, width)
        assert " ".join(lines).split() == words
        assert all(len(line) <= width or " " not in line for line in lines)
        for current, following in zip(lines, lines[1:], strict=False):
            assert len(current) + 1 + len(following.split()[0]) > width
