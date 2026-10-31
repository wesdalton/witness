"""Run-length encoding of digit-free strings: 'aaab' <-> '3a1b'."""

from __future__ import annotations


def encode(text: str) -> str:
    if any(ch.isdigit() for ch in text):
        raise ValueError("digits cannot be encoded")
    out = []
    i = 0
    while i < len(text):
        j = i
        while j < len(text) and text[j] == text[i]:
            j += 1
        out.append(f"{j - i}{text[i]}")
        i = j
    return "".join(out)


def decode(data: str) -> str:
    out = []
    count = 0
    for ch in data:
        if ch.isdigit():
            count = int(ch)
        else:
            if count == 0:
                raise ValueError(f"missing count before {ch!r}")
            out.append(ch * count)
            count = 0
    if count:
        raise ValueError("trailing count without a character")
    return "".join(out)
