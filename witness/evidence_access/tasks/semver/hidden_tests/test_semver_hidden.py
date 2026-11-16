import pytest

from semver import compare, latest, parse, sort_versions


def test_release_sorts_after_its_prerelease():
    assert compare("1.0.0-rc.1", "1.0.0") == -1
    assert compare("1.0.0", "1.0.0-rc.1") == 1


def test_numeric_fields_compare_numerically():
    assert compare("1.10.0", "1.9.0") == 1


def test_major_dominates():
    assert compare("2.0.0", "1.99.99") == 1


def test_equal_versions():
    assert compare("3.2.1", "3.2.1") == 0


def test_numeric_prerelease_identifiers():
    assert compare("1.0.0-rc.2", "1.0.0-rc.10") == -1


def test_alphanumeric_after_numeric_identifier():
    assert compare("1.0.0-1", "1.0.0-alpha") == -1


def test_shorter_prerelease_sorts_first():
    assert compare("1.0.0-alpha", "1.0.0-alpha.1") == -1


def test_sort_versions_full_order():
    versions = ["1.0.0", "1.0.0-beta", "0.9.9", "1.0.0-alpha", "1.0.1"]
    assert sort_versions(versions) == ["0.9.9", "1.0.0-alpha", "1.0.0-beta", "1.0.0", "1.0.1"]


def test_latest_prefers_release():
    assert latest(["2.0.0-rc.3", "2.0.0", "1.9.9"]) == "2.0.0"


def test_latest_empty_rejected():
    with pytest.raises(ValueError):
        latest([])


@pytest.mark.parametrize("bad", ["1.0", "1.0.0.0", "a.b.c", "1.0.0-", "1.0.0-rc..1"])
def test_invalid_versions_rejected(bad):
    with pytest.raises(ValueError):
        parse(bad)
