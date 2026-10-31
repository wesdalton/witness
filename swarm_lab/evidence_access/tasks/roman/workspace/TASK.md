# Task: fix the roman bug

One behavior of `roman` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

`to_roman` converts 1..3999 to canonical Roman numerals. `from_roman` parses canonical numerals, including repeated symbols such as `XX` and subtractive pairs such as `CM`, and rejects anything else.
