import copy
import json
from decimal import Decimal

import pytest

from swarm_lab import query_study
from swarm_lab.agent_budget import PhaseBudget
from swarm_lab.pilot import BudgetError
from swarm_lab.query_study import initial_view, run_episode, validate_submission
from swarm_lab.reconciliation_cases import ReconciliationWorkspace


def answer():
    return {"verdict": "supported", "p_support": 0.9, "audit_sql": "SELECT 7",
            "evidence_ids": ["report"], "justification": "Scripted infrastructure test."}


def test_query_view_hides_truth_and_timing():
    a, b = ReconciliationWorkspace(8001, True, revision=2), \
        ReconciliationWorkspace(8001, False, revision=2)
    try:
        for arm in ("no_peers", "neutral", "endorsement"):
            assert initial_view(a, arm, {"exit_code": 0, "elapsed_seconds": 0.3}) == \
                initial_view(b, arm, {"exit_code": 0, "elapsed_seconds": 0.9})
        neutral = initial_view(a, "neutral", {"exit_code": 0})
        endorsed = initial_view(a, "endorsement", {"exit_code": 0})
        for key in neutral:
            if key != "peer_messages":
                assert neutral[key] == endorsed[key]
    finally:
        a.close()
        b.close()


def test_query_submission_rejects_bad_probabilities_and_unavailable_evidence():
    validate_submission(answer(), {"report"})
    for bad in (float("nan"), True, -0.1, 1.1):
        value = answer()
        value["p_support"] = bad
        with pytest.raises(ValueError):
            validate_submission(value, {"report"})
    value = answer()
    value["evidence_ids"] = ["unseen"]
    with pytest.raises(ValueError, match="evidence"):
        validate_submission(value, {"report"})


def test_final_artifact_evaluation_never_enters_agent_context(tmp_path, monkeypatch):
    class FakeWorkspace:
        def __init__(self, *args, **kwargs):
            self.report = {"net_shipped_units": 7}
            self.expected = 7

        def hashes(self):
            return {"records.sqlite": "dummy"}

        def execute(self, *args):
            return {"exit_code": 0, "timed_out": False, "output_truncated": False,
                    "stdout": '{"rows":[[7]],"rows_truncated":false}', "stderr": ""}

        def close(self):
            pass

    class ScriptedClient:
        def generate(self, messages, final=False):
            self.received = copy.deepcopy(messages)
            call = {"id": "scripted", "function": {
                "name": "submit", "arguments": json.dumps(answer())}}
            return {"tool_calls": [call]}, {"finish_reason": "tool_calls"}

    monkeypatch.setattr(query_study, "ReconciliationWorkspace", FakeWorkspace)
    client = ScriptedClient()
    record = run_episode({"id": "episode-001", "seed": 8001, "truth": True,
                          "arm": "no_peers"}, tmp_path, client, "unused")
    assert record["status"] == "completed"
    assert record["metrics"]["audit_sql_correct_this_database"]
    assert len(client.received) == 2
    assert "actual_total" not in client.received[1]["content"]
    assert "artifact_evaluation" not in client.received[1]["content"]


def test_query_tools_meet_strict_schema_requirements(tmp_path):
    client = query_study.StrictQueryClient(
        "test", "openai/gpt-6-luna", PhaseBudget(tmp_path / "ledger"), "test",
        Decimal(1), Decimal(".000000125"), Decimal(".0000005"), tools=query_study.TOOLS)
    value = client.payload([{"role": "system", "content": "test"},
                            {"role": "user", "content": "case"}], False)
    for tool in value["tools"]:
        schema = tool["parameters"]
        assert tool["strict"] is True
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])


def test_development_hold_stops_before_creating_a_batch(tmp_path, monkeypatch):
    output = tmp_path / "undispatched"
    monkeypatch.setattr(query_study, "LIVE_HOLD_REASON", "test design hold")
    monkeypatch.setattr("sys.argv", ["query_study", "--live", "--out", str(output)])
    with pytest.raises(BudgetError, match="test design hold"):
        query_study.main()
    assert not output.exists()
