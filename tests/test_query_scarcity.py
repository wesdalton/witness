import json

from swarm_lab import query_study


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


def test_one_credit_forces_submission_and_keeps_grading_private(tmp_path, monkeypatch):
    result = {"exit_code": 0, "timed_out": False, "output_truncated": False,
              "stdout": '{"rows":[[7]],"rows_truncated":false}'}
    executions = []

    def execute(workspace, sql):
        executions.append(sql)
        return result

    class ScriptedClient:
        def __init__(self):
            self.flags = []

        def generate(self, messages, final):
            self.flags.append(final)
            if len(self.flags) == 1:
                assert "one live query" in messages[0]["content"]
                assert json.loads(messages[1]["content"])["max_queries"] == 1
                name, value = "query", {"sql": "SELECT 7"}
            else:
                assert final
                assert json.loads(messages[-1]["content"])["queries_remaining"] == 0
                name, value = "submit", {
                    "verdict": "supported", "p_support": 0.9, "evidence_ids": ["query:1"],
                    "audit_sql": "SELECT 7", "justification": "Scripted test only."}
            call = {"id": f"call-{len(self.flags)}", "function": {
                "name": name, "arguments": json.dumps(value)}}
            return {"tool_calls": [call]}, {"finish_reason": "tool_calls"}

    monkeypatch.setattr(query_study, "ReconciliationWorkspace", FakeWorkspace)
    monkeypatch.setattr(query_study, "execute_query", execute)
    client = ScriptedClient()
    record = query_study.run_episode(
        {"id": "episode-001", "seed": 1, "truth": True, "arm": "no_peers",
         "query_budget": 1}, tmp_path, client, "unused")
    assert record["status"] == "completed"
    assert client.flags == [False, True]
    assert len(executions) == 2  # one live call and one private final-artifact grade
    assert sum(e["type"] == "tool" for e in record["events"]) == 1


def test_overbudget_bundle_executes_no_partial_query(tmp_path, monkeypatch):
    class ScriptedClient:
        def generate(self, messages, final):
            calls = [{"id": str(i), "function": {
                "name": "query", "arguments": '{"sql":"SELECT 7"}'}} for i in range(2)]
            return {"tool_calls": calls}, {"finish_reason": "tool_calls"}

    def forbidden(*args):
        raise AssertionError("No query in an over-budget bundle may execute")

    monkeypatch.setattr(query_study, "ReconciliationWorkspace", FakeWorkspace)
    monkeypatch.setattr(query_study, "execute_query", forbidden)
    record = query_study.run_episode(
        {"id": "episode-001", "seed": 1, "truth": True, "arm": "no_peers",
         "query_budget": 1}, tmp_path, ScriptedClient(), "unused")
    assert record["status"] == "invalid_action"
    assert not any(e["type"] == "tool" for e in record["events"])
