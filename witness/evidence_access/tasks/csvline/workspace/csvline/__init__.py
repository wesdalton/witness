"""Split and join single CSV lines with double-quote escaping."""

from __future__ import annotations


def split_line(line: str, sep: str = ",") -> list[str]:
    fields: list[str] = []
    buffer: list[str] = []
    quoted = False
    i = 0
    while i < len(line):
        ch = line[i]
        if quoted:
            if ch == '"':
                quoted = False
            else:
                buffer.append(ch)
        elif ch == '"' and not buffer:
            quoted = True
        elif ch == sep:
            fields.append("".join(buffer))
            buffer = []
        else:
            buffer.append(ch)
        i += 1
    if quoted:
        raise ValueError("unterminated quoted field")
    fields.append("".join(buffer))
    return fields


def join_line(fields: list[str], sep: str = ",") -> str:
    out = []
    for field in fields:
        if any(c in field for c in (sep, '"', "\n")) or field != field.strip():
            field = '"' + field.replace('"', '""') + '"'
        out.append(field)
    return sep.join(out)
