import pytest

from csvline import join_line, split_line


def test_plain_fields():
    assert split_line("a,b,c") == ["a", "b", "c"]


def test_quoted_field_with_separator():
    assert split_line('"a,b",c') == ["a,b", "c"]


def test_doubled_quote_is_literal_quote():
    assert split_line('"say ""hi""",x') == ['say "hi"', "x"]


def test_field_that_is_only_a_quote():
    assert split_line('""""') == ['"']


def test_empty_fields():
    assert split_line(",,") == ["", "", ""]


def test_empty_quoted_field():
    assert split_line('"",a') == ["", "a"]


def test_unterminated_quote_rejected():
    with pytest.raises(ValueError):
        split_line('"abc')


def test_custom_separator():
    assert split_line('a;"b;c"', sep=";") == ["a", "b;c"]


@pytest.mark.parametrize("fields", [
    ["plain", "with,comma"],
    ['quote"inside', ""],
    [" padded ", 'mix,"all"'],
])
def test_round_trip(fields):
    assert split_line(join_line(fields)) == fields
