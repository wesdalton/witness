import json

import pytest

from swarm_lab.core.archive import Archive, bootstrap_legacy, write_once


def experiment(tmp_path):
    archive = Archive(tmp_path)
    folder = archive.create_experiment("test-study", "Test", "Question", "# Protocol\n")
    return archive, folder


def test_existing_design_run_and_report_cannot_be_replaced(tmp_path):
    archive, folder = experiment(tmp_path)
    with pytest.raises(FileExistsError):
        archive.create_experiment("test-study", "Changed", "Changed", "Changed")
    run = archive.new_bundle("test-study", "runs", "pilot-01")
    write_once(run / "result.json", {"status": "completed"})
    with pytest.raises(FileExistsError):
        archive.new_bundle("test-study", "runs", "pilot-01")
    with pytest.raises(FileExistsError):
        write_once(run / "result.json", {"status": "different"})
    archive.seal("test-run", run, kind="run", title="Run", experiment="test-study",
                 parents=["test-study.design"])
    with pytest.raises(FileExistsError):
        archive.seal("another-id", run, kind="run", title="Copy", experiment="test-study")
    assert json.loads((run / "result.json").read_text())["status"] == "completed"
    assert (folder / "design/protocol.md").read_text() == "# Protocol\n"


@pytest.mark.parametrize("change", ["edit", "add", "delete"])
def test_audit_detects_any_change_to_a_completed_bundle(tmp_path, change):
    archive, folder = experiment(tmp_path)
    path = folder / "design/protocol.md"
    if change == "edit":
        path.write_text("changed")
    elif change == "add":
        (folder / "design/extra.txt").write_text("extra")
    else:
        path.unlink()
    assert archive.audit()["errors"]


def test_correction_is_separate_and_preserves_prior_evidence(tmp_path):
    archive, folder = experiment(tmp_path)
    correction = archive.new_bundle("test-study", "adjudications", "correction-01")
    write_once(correction / "report.md", "Correction; do not rewrite protocol.\n")
    archive.seal("correction", correction, kind="adjudication", title="Correction",
                 experiment="test-study", parents=["test-study.design"])
    archive.build_index()
    assert not archive.audit()["errors"]
    assert (folder / "design/protocol.md").read_text() == "# Protocol\n"


def test_paths_symlinks_and_missing_lineage_are_rejected(tmp_path):
    archive, folder = experiment(tmp_path)
    with pytest.raises(ValueError):
        archive.inventory("../outside")
    (folder / "design/link").symlink_to(folder / "design/protocol.md")
    with pytest.raises(ValueError):
        archive.inventory(folder / "design")
    (folder / "design/link").unlink()
    write_once(folder / "unlinked.md", "Report\n")
    with pytest.raises(ValueError, match="parent"):
        archive.seal("bad", folder / "unlinked.md", kind="report",
                     title="Bad", experiment="test-study", parents=["absent"])


def test_alias_paths_and_nested_seals_do_not_duplicate_evidence(tmp_path):
    archive, folder = experiment(tmp_path)
    with pytest.raises(FileExistsError):
        archive.seal("alias", folder / "design/../design", kind="design",
                     title="Alias", experiment="test-study")
    with pytest.raises(FileExistsError, match="overlaps"):
        archive.seal("nested", folder / "design/protocol.md", kind="report",
                     title="Nested", experiment="test-study")


def test_legacy_import_is_idempotent_and_preserves_living_report_editions(tmp_path):
    for group in ("swarm", "agent-study", "portfolio"):
        (tmp_path / "research" / group).mkdir(parents=True)
    base = tmp_path / "research/portfolio"
    write_once(base / "pilot/manifest.json", {"batch": "test"})
    write_once(base / "report.md", "First edition\n")
    write_once(base / "analysis.json", {"finding": 1})
    first = bootstrap_legacy(tmp_path)
    assert not first["errors"] and first["bundles"] == 3
    assert bootstrap_legacy(tmp_path) == first
    (base / "report.md").write_text("Second edition\n")
    second = bootstrap_legacy(tmp_path)
    assert not second["errors"] and second["bundles"] == 4
    copies = list((tmp_path / "research/archive/legacy-writeups/portfolio").glob("*.md"))
    assert {p.read_text() for p in copies} == {"First edition\n", "Second edition\n"}
