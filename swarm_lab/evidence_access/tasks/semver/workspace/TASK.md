# Task: fix the semver bug

One behavior of `semver` is wrong. Fix it without changing the public API.
A hidden test suite runs after you submit.

## Spec

Versions follow MAJOR.MINOR.PATCH[-PRERELEASE]. A prerelease sorts before its release; numeric prerelease identifiers sort numerically and before alphanumeric ones.
