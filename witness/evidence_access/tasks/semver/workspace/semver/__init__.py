"""Semantic version parsing and ordering (MAJOR.MINOR.PATCH[-PRERELEASE])."""

from __future__ import annotations

from typing import NamedTuple


class Version(NamedTuple):
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()


def parse(text: str) -> Version:
    core, dash, pre = text.partition("-")
    parts = core.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"invalid version: {text!r}")
    identifiers = tuple(pre.split(".")) if dash else ()
    if any(not i for i in identifiers):
        raise ValueError(f"empty prerelease identifier: {text!r}")
    return Version(int(parts[0]), int(parts[1]), int(parts[2]), identifiers)


def _identifier(value: str) -> tuple[int, int, str]:
    # Numeric identifiers sort numerically and before alphanumeric ones.
    return (0, int(value), "") if value.isdigit() else (1, 0, value)


def sort_key(version: Version) -> tuple:
    release = len(version.prerelease) > 0
    return (version.major, version.minor, version.patch, release,
            tuple(_identifier(i) for i in version.prerelease))


def compare(a: str, b: str) -> int:
    left, right = sort_key(parse(a)), sort_key(parse(b))
    return (left > right) - (left < right)


def sort_versions(versions: list[str]) -> list[str]:
    return sorted(versions, key=lambda v: sort_key(parse(v)))


def latest(versions: list[str]) -> str:
    if not versions:
        raise ValueError("no versions")
    return sort_versions(versions)[-1]
