"""Roman numerals for 1 through 3999, in canonical form only."""

from __future__ import annotations

VALUES = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
          (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
SYMBOLS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def to_roman(number: int) -> str:
    if not 1 <= number <= 3999:
        raise ValueError(f"{number} is outside 1..3999")
    out = []
    for value, symbol in VALUES:
        while number >= value:
            out.append(symbol)
            number -= value
    return "".join(out)


def from_roman(text: str) -> int:
    if not text or any(ch not in SYMBOLS for ch in text):
        raise ValueError(f"not a roman numeral: {text!r}")
    total = 0
    for i, ch in enumerate(text):
        value = SYMBOLS[ch]
        if i + 1 < len(text) and value <= SYMBOLS[text[i + 1]]:
            total -= value
        else:
            total += value
    if to_roman(total) != text:
        raise ValueError(f"non-canonical numeral: {text!r}")
    return total
