"""Greedy word wrapping to a fixed width."""

from __future__ import annotations


def wrap(text: str, width: int) -> list[str]:
    """Lines of at most `width` characters, broken at whitespace.

    A word longer than `width` occupies its own line unbroken.
    """
    if width < 1:
        raise ValueError("width must be positive")
    lines: list[str] = []
    line = ""
    for word in text.split():
        if not line:
            line = word
        elif len(line) + 1 + len(word) < width:
            line += " " + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def fill(text: str, width: int) -> str:
    return "\n".join(wrap(text, width))
