import json
from types import SimpleNamespace

import pytest

from swarm_lab import query_interfaces, query_study, route_cases
from swarm_lab.query_study import FIELDS, ROUTE_TOOLS, initial_view, validate_submission


def test_output_intervention_changes_only_required_program_instruction_and_schema():
    p_system, p_tools = query_interfaces.interface("program", ROUTE_TOOLS[0], FIELDS)
    v_system, v_tools = query_interfaces.interface("verdict", ROUTE_TOOLS[0], FIELDS)
    assert p_system == v_system + query_interfaces.PROGRAM_PARAGRAPH
    assert p_tools[0] == v_tools[0]
    p_schema, v_schema = (tools[1]["function"]["parameters"] for tools in (p_tools, v_tools))
    assert {k: v for k, v in p_schema["properties"].items() if k != "audit_sql"} == \
        v_schema["properties"]
    assert set(p_schema["required"]) - {"audit_sql"} == set(v_schema["required"])
    assert p_schema["additionalProperties"] is v_schema["additionalProperties"] is False


def test_initial_factual_view_identical_between_output_modes():
    workspace = SimpleNamespace(
        contract=route_cases.CONTRACT, schema=route_cases.SCHEMA,
        parameters=route_cases.PARAMETERS, claim="Route claim", report={"minimum_total_cost": 7},
        inherited_query=route_cases.GREEDY_SQL, inherited_execution={"exit_code": 0})
    for arm in ("neutral", "endorsement"):
        program = initial_view(workspace, arm, {"exit_code": 0}, "program")
        verdict = initial_view(workspace, arm, {"exit_code": 0}, "verdict")
        assert program == verdict
        assert "audit_sql" not in program["contract"]
        assert "risk group" in program["contract"]


def test_verdict_submission_has_no_imputed_artifact(tmp_path, monkeypatch):
    value = {"verdict": "supported", "p_support": 0.9, "evidence_ids": ["report"],
             "justification": "Scripted interface test, not model research."}
    validate_submission(value, {"report"}, program_required=False)
    with pytest.raises(ValueError):
        validate_submission(value, {"report"}, program_required=True)

    class FakeWorkspace:
        def __init__(self, *args, **kwargs):
            self.report = {"net_shipped_units": 7}
            self.expected = 7

        def hashes(self):
            return {}

        def execute(self, *args):
            return {"exit_code": 0, "timed_out": False, "output_truncated": False}

        def close(self):
            pass

    class ScriptedClient:
        def generate(self, messages, final):
            call = {"id": "scripted", "function": {
                "name": "submit", "arguments": json.dumps(value)}}
            return {"tool_calls": [call]}, {"finish_reason": "tool_calls"}

    monkeypatch.setattr(query_study, "ReconciliationWorkspace", FakeWorkspace)

    def forbidden(*args):
        raise AssertionError("No final program was requested or submitted")

    monkeypatch.setattr(query_study, "execute_query", forbidden)
    record = query_study.run_episode(
        {"id": "episode-001", "seed": 1, "truth": True, "arm": "neutral",
         "output_mode": "verdict"}, tmp_path, ScriptedClient(), "unused")
    assert record["status"] == "completed"
    assert record["metrics"]["correct_verdict"] is True
    assert record["metrics"]["audit_sql_correct_this_database"] is None
    assert "artifact_evaluation" not in record
