import pytest

from rle import decode, encode


def test_encode_runs():
    assert encode("aaab") == "3a1b"


def test_decode_runs():
    assert decode("3a1b") == "aaab"


def test_multi_digit_count():
    assert decode("12x") == "x" * 12


def test_empty_string():
    assert encode("") == "" and decode("") == ""


def test_digits_cannot_be_encoded():
    with pytest.raises(ValueError):
        encode("a1")


@pytest.mark.parametrize("data", ["a", "3a2", "0a"])
def test_malformed_encodings_rejected(data):
    with pytest.raises(ValueError):
        decode(data)


def test_round_trip_long_runs():
    for n in range(1, 120):
        text = "a" * n + "b" + "c" * (n % 7 + 1)
        assert decode(encode(text)) == text
