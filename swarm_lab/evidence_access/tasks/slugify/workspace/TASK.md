# Task: fix the slugify bug

One behavior of `slugify` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

`slugify(title, max_length=50)` returns lowercase ASCII words joined by single hyphens, with no leading or trailing hyphen, cut at a word boundary when too long.
