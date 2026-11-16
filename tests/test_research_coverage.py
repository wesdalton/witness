import importlib.util
from pathlib import Path

import pytest

from witness.core.archive import Archive, write_once

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "coverage_audit", ROOT / "scripts/audit_research_coverage.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

HEADER = b'{"type":"authorization"}\n'


def ledger(tmp_path, raw=HEADER):
    path = tmp_path / audit.LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


def test_unsealed_experiment_file_is_reported_until_its_bundle_is_sealed(tmp_path):
    ledger(tmp_path)
    archive = Archive(tmp_path)
    archive.create_experiment("study", "Study", "Question", "# Protocol\n")
    run = archive.new_bundle("study", "runs", "run-01")
    write_once(run / "episode-0000.json", {"status": "completed"})
    result = audit.coverage(tmp_path)
    assert result["unregistered"] == ["research/experiments/study/runs/run-01/episode-0000.json"]
    assert audit.failed(result)
    archive.seal("study.run-01", run, kind="run", title="Run", experiment="study",
                 parents=["study.design"])
    result = audit.coverage(tmp_path)
    assert not result["unregistered"] and not result["integrity"]["errors"]
    assert not audit.failed(result)


def test_edited_sealed_file_fails_integrity(tmp_path):
    ledger(tmp_path)
    archive = Archive(tmp_path)
    folder = archive.create_experiment("study", "Study", "Question", "# Protocol\n")
    (folder / "design/protocol.md").write_text("changed\n")
    assert audit.failed(audit.coverage(tmp_path))


def test_ledger_can_append_but_cannot_rewrite_a_committed_edition(tmp_path):
    path = ledger(tmp_path, HEADER + b'{"type":"reserve"}\n')
    result = audit.ledger_check(tmp_path, [("a", HEADER), ("b", HEADER + b'{"type":"reserve"}\n')])
    assert result["editions_checked"] == 2 and not result["rewritten_editions"]
    path.write_bytes(b'{"type":"different"}\n')
    result = audit.ledger_check(tmp_path, [("a", HEADER)])
    assert result["rewritten_editions"] == ["a"]


def test_missing_ledger_fails(tmp_path):
    result = audit.coverage(tmp_path)
    assert not result["ledger"]["present"] and audit.failed(result)


def test_repository_ledger_history_follows_the_move():
    editions = audit.committed_editions(ROOT)
    if editions is None:
        pytest.skip("source copy without git history")
    assert editions, "the committed ledger history should be found under either path"
    result = audit.ledger_check(ROOT, editions)
    assert result["editions_checked"] == len(editions) and not result["rewritten_editions"]
