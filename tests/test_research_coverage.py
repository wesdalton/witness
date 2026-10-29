import importlib.util
from pathlib import Path

from swarm_lab.core.archive import write_once

spec = importlib.util.spec_from_file_location(
    "coverage_audit", Path(__file__).resolve().parents[1] / "scripts/audit_research_coverage.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_ignored_log_is_reported_then_archived_without_modifying_it(tmp_path):
    log = tmp_path / "logs/smoke.eval"
    write_once(log, "historical binary stand-in")
    assert audit.coverage(tmp_path)["unregistered"] == ["logs/smoke.eval"]
    audit.capture_legacy(tmp_path)
    assert not audit.coverage(tmp_path)["unregistered"]
    assert log.read_text() == "historical binary stand-in"
    assert not audit.coverage(tmp_path)["integrity"]["errors"]


def test_ledger_can_append_but_cannot_erase_an_archived_prefix(tmp_path):
    ledger = tmp_path / "research/agent-study/budget.jsonl"
    write_once(ledger, '{"type":"authorization"}\n')
    audit.capture_legacy(tmp_path)
    with ledger.open("a") as stream:
        stream.write('{"type":"reserve"}\n')
    assert not audit.coverage(tmp_path)["changed_unarchived_editions"]
    ledger.write_text('{"type":"different"}\n')
    assert audit.coverage(tmp_path)["changed_unarchived_editions"] == [
        "research/agent-study/budget.jsonl"]


def test_changed_writeup_needs_new_edition(tmp_path):
    report = tmp_path / "research/overview.md"
    write_once(report, "Edition one")
    audit.capture_legacy(tmp_path)
    report.write_text("Edition two")
    assert audit.coverage(tmp_path)["changed_unarchived_editions"] == ["research/overview.md"]
    audit.capture_legacy(tmp_path)
    assert not audit.coverage(tmp_path)["changed_unarchived_editions"]
