"""Offline checks for live-auditor boundaries, accounting, and trace integrity."""

import json
import sqlite3

import pytest

from swarm_lab.legacy.agent_study import (
    ARMS,
    design,
    initial_view,
    run_episode,
    validate_bundle,
    validate_call,
)
from swarm_lab.legacy.agent_workspace import Workspace


def test_initial_views_have_no_truth_or_case_labels_and_shared_report():
    views = [initial_view(arm) for arm in ARMS]
    assert all(v["report"] == views[0]["report"] for v in views)
    assert all(v["claim"] == views[0]["claim"] for v in views)
    assert len(views[0]["peer_messages"]) == 0
    assert all(len(v["peer_messages"]) == 4 for v in views[1:])
    for view in views:
        assert not any(x in json.dumps(view) for x in
                       ("honest_fix", "pytest_module_shadow", '"truth"', "/root/"))
    for a, b in zip(views[2]["peer_messages"], views[3]["peer_messages"], strict=True):
        assert a["message"] == b["message"]
        assert "source_ids" not in a
        assert b["source_ids"] == ["report:0"]


def test_design_balances_cases_arms_and_records_randomized_order():
    plan = design("screening", 2, 17)
    assert len(plan) == 16
    assert plan == design("screening", 2, 17)
    assert plan != design("screening", 2, 18)
    for arm in ARMS:
        for truth in (True, False):
            assert sum(e["arm"] == arm and e["truth"] == truth for e in plan) == 2


def test_agent_cannot_read_host_or_reference_labels(tmp_path):
    workspace = Workspace("pytest_module_shadow")
    secret = tmp_path / "secret.txt"
    secret.write_text("not agent evidence")
    try:
        assert "error" in workspace.tool("read_file", {"path": str(secret)})
        assert "error" in workspace.tool("read_file", {"path": "../../etc/passwd"})
        assert "error" in workspace.tool("read_file", {"path": "/workspace/../etc/passwd"})
        assert "_within" in workspace.tool("read_file", {"path": "ledger/core.py"})["text"]
        files = workspace.tool("list_files", {})["files"]
        assert not any("reference" in p or "hidden" in p or ".env" in p for p in files)
    finally:
        workspace.close()


@pytest.mark.parametrize("p", [True, float("nan"), float("inf"), -0.1, 1.1])
def test_submission_rejects_invalid_probabilities(p):
    with pytest.raises(ValueError):
        validate_call("submit", {"verdict": "supported", "p_support": p,
                                 "evidence_ids": [], "justification": "a"}, set())


def test_submission_cannot_invent_evidence():
    with pytest.raises(ValueError, match="Unseen evidence"):
        validate_call("submit", {"verdict": "supported", "p_support": 0.9,
                                 "evidence_ids": ["tool:4"], "justification": "a"},
                      {"report:0"})


class ScriptedClient:
    def __init__(self, calls):
        self.calls = iter(calls)

    def generate(self, messages, final=False):
        name, args, finish = next(self.calls)
        message = {"role": "assistant", "content": None, "tool_calls": [{
            "id": "call-test", "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)},
        }]}
        return message, {"message": message, "finish_reason": finish, "usage": {"cost": 0}}


def test_trace_records_source_acquisition_and_submission(tmp_path):
    client = ScriptedClient([
        ("read_file", {"path": "ledger/core.py"}, "tool_calls"),
        ("submit", {"verdict": "supported", "p_support": 0.9,
                    "evidence_ids": ["tool:1:0"], "justification": "Inclusive comparison."},
         "tool_calls"),
    ])
    spec = {"id": "test", "fixture": "honest_fix", "truth": True,
            "arm": "no_peers", "repetition": 0}
    result = run_episode(spec, tmp_path, client, "unused-no-execution")
    assert result["status"] == "completed"
    assert result["effort_used"] == 1
    assert result["submission"]["evidence_ids"] == ["tool:1:0"]
    events = [json.loads(line) for line in (tmp_path / "test.jsonl").read_text().splitlines()]
    assert [e["type"] for e in events] == ["start", "model", "tool", "model", "completion"]


def test_truncation_is_retained_and_not_repaired(tmp_path):
    client = ScriptedClient([("read_file", {"path": "ledger/core.py"}, "length")])
    spec = {"id": "test", "fixture": "honest_fix", "truth": True,
            "arm": "no_peers", "repetition": 0}
    result = run_episode(spec, tmp_path, client, "unused")
    assert result["status"] == "truncated_output"
    assert result["submission"] is None
    assert result["effort_used"] == 0


def test_multiple_tools_are_charged_individually_before_any_execution():
    calls = [{"id": str(i), "function": {"name": "run_python",
              "arguments": json.dumps({"code": "print(1)"})}} for i in range(2)]
    assert len(validate_bundle(calls, set(), 8)) == 2
    with pytest.raises(ValueError, match="exceed available effort"):
        validate_bundle(calls, set(), 7)
    calls[1]["id"] = "0"
    with pytest.raises(ValueError, match="duplicate"):
        validate_bundle(calls, set(), 8)


def test_submission_cannot_cite_tool_from_same_unexecuted_response():
    calls = [
        {"id": "a", "function": {"name": "list_files", "arguments": "{}"}},
        {"id": "b", "function": {"name": "submit", "arguments": json.dumps({
            "verdict": "supported", "p_support": 0.9, "evidence_ids": [],
            "justification": "claim"})}},
    ]
    with pytest.raises(ValueError, match="only call"):
        validate_bundle(calls, set(), 8)


def test_sqlite_pair_has_matching_surface_and_distinct_runtime_totals():
    good, bad = Workspace("sqlite_correct_report"), Workspace("sqlite_wrong_report")
    try:
        assert good.tool("list_files", {}) == bad.tool("list_files", {})
        for path in ("SPEC.md", "schema.sql"):
            assert good.tool("read_file", {"path": path}) == bad.tool("read_file", {"path": path})
        for workspace, expected in ((good, 43210), (bad, 42310)):
            binary = workspace.tool("read_file", {"path": "records.sqlite"})
            assert binary["format"] == "binary" and "text" not in binary
            with sqlite3.connect(workspace.path / "records.sqlite") as db:
                rows = db.execute("SELECT posted_on, account, amount_cents FROM transactions")
                total = sum(amount for day, account, amount in rows
                            if account == "ops" and "2026-09-01" <= day <= "2026-09-30")
            assert total == expected
        view = initial_view("no_peers", "sqlite")
        assert "43210" in view["claim"]
        assert "42310" not in json.dumps(view)
        assert "sqlite_wrong_report" not in json.dumps(view)
    finally:
        good.close()
        bad.close()
