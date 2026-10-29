# Task: fix the csvline bug

One behavior of `csvline` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

`split_line` splits one CSV line. Quoted fields may contain the separator, and a doubled quote inside a quoted field is a literal quote. `join_line` is its inverse.
