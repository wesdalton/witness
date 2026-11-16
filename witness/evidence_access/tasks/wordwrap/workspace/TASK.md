# Task: fix the wordwrap bug

One behavior of `wordwrap` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

`wrap(text, width)` greedily packs words into lines of at most `width` characters; a line may be exactly `width` long. Longer words get their own line.
