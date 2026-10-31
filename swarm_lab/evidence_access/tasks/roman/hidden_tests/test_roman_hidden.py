import pytest

from roman import from_roman, to_roman


def test_to_roman_examples():
    numbers = (1, 4, 9, 14, 40, 90, 400, 1994, 3999)
    assert [to_roman(n) for n in numbers] == [
        "I", "IV", "IX", "XIV", "XL", "XC", "CD", "MCMXCIV", "MMMCMXCIX"]


def test_from_roman_repeated_symbols():
    assert [from_roman(s) for s in ("III", "XX", "CCC")] == [3, 20, 300]


def test_from_roman_subtractive_pairs():
    assert from_roman("MCMXCIV") == 1994
    assert from_roman("XLII") == 42


def test_round_trip_full_range():
    for number in range(1, 4000):
        assert from_roman(to_roman(number)) == number


@pytest.mark.parametrize("text", ["", "IIII", "IC", "VX", "ABC", "MMMM"])
def test_malformed_numerals_rejected(text):
    with pytest.raises(ValueError):
        from_roman(text)


@pytest.mark.parametrize("number", [0, -1, 4000])
def test_out_of_range_rejected(number):
    with pytest.raises(ValueError):
        to_roman(number)
