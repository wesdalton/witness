# Task: fix the rle bug

One behavior of `rle` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

`encode` writes each run as its length followed by the character (`aaab` -> `3a1b`). `decode` reverses it, including counts with several digits, and rejects malformed input.
